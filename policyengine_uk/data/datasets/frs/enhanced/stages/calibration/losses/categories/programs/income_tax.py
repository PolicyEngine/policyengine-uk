import numpy as np
from ...loss_category import LossCategory
import tensorflow as tf
from typing import Iterable, Tuple
from policyengine_core.taxscales import SingleAmountTaxScale


class IncomeTax(LossCategory):
    name = "Income Tax"
    category = "Programs"
    variable = "income_tax"

    def initialise(self):
        income_tax = self.sim.calc("income_tax", period=self.year).values
        total_income = self.sim.calc(
            "adjusted_net_income", period=self.year
        ).values
        countries = self.sim.calc("country", period=self.year).values
        household_income_tax = self.sim.calc(
            "income_tax", period=self.year, map_to="household"
        ).values

        it = self.calibration_parameters.programs.income_tax

        self.comparisons = []

        # Revenue by country

        for country in ("ENGLAND", "WALES", "NORTHERN_IRELAND", "SCOTLAND"):
            self.comparisons += [
                (
                    f"income_tax_{country}",
                    household_income_tax * (countries == country),
                    it.budgetary_impact.by_country._children[country],
                )
            ]

        self.comparisons += [
            (
                "income_tax_UNITED_KINGDOM",
                household_income_tax,
                it.budgetary_impact.by_country._children["UNITED_KINGDOM"],
            )
        ]

        # Revenue by income band

        scale = it.budgetary_impact.by_income

        for i in range(len(scale.thresholds)):
            lower_threshold = scale.thresholds[i]
            upper_threshold = (
                scale.thresholds[i + 1]
                if i < len(scale.thresholds) - 1
                else np.inf
            )

            income_is_in_band = (total_income >= lower_threshold) * (
                total_income < upper_threshold
            )
            household_values = self.sim.map_result(
                income_tax * income_is_in_band, "person", "household"
            )

            amount = scale.amounts[i]
            self.comparisons += [
                (
                    f"income_tax_by_income_{i}",
                    household_values,
                    amount,
                )
            ]

        # Taxpayers by country and income band

        tax_band = self.sim.calc("tax_band", period=self.year).values
        tax_band = np.select(
            [
                tax_band == "STARTER",
                tax_band == "INTERMEDIATE",
                True,
            ],
            [
                "BASIC",
                "BASIC",
                tax_band,
            ],
        )

        person_country = self.sim.calc(
            "country", period=self.year, map_to="person"
        ).values

        for country in ("ENGLAND", "WALES", "NORTHERN_IRELAND", "SCOTLAND"):
            for band in ("BASIC", "HIGHER", "ADDITIONAL"):
                self.comparisons += [
                    (
                        f"income_tax_payers_{country}_{band}",
                        self.sim.map_result(
                            (income_tax > 0)
                            * (person_country == country)
                            * (tax_band == band),
                            "person",
                            "household",
                        ),
                        it.participants.by_country_and_band._children[
                            country
                        ]._children[band],
                    )
                ]

    def get_loss_subcomponents(
        self, household_weights: tf.Tensor
    ) -> Iterable[Tuple]:
        for name, values, actual in self.comparisons:
            yield name, tf.reduce_sum(values * household_weights), actual

    def get_metric_names(self) -> Iterable[str]:
        return [x[0] for x in self.comparisons]
