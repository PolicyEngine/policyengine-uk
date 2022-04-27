import numpy as np
from ...loss_category import LossCategory
import tensorflow as tf
from typing import Iterable, Tuple

class IncomeTax(LossCategory):
    name = "Income Tax"
    category = "Programs"

    def initialise(self):
        income_tax = self.sim.calc("income_tax", period=self.year).values
        total_income = self.sim.calc("adjusted_net_income", period=self.year).values
        countries = self.sim.calc("country", period=self.year).values
        household_income_tax = self.sim.calc("income_tax", period=self.year, map_to="household").values

        it = self.calibration_parameters.programs.income_tax

        self.comparisons = []

        # Revenue by country

        for country in ("ENGLAND", "WALES", "NORTHERN_IRELAND", "SCOTLAND"):
            self.comparisons += [(
                f"income_tax_{country}",
                household_income_tax * (countries == country),
                it._children[country]
            )]
        
        self.comparisons += [
            "income_tax_UNITED_KINGDOM",
            household_income_tax,
            it._children["UNITED_KINGDOM"]
        ]

        # Revenue by income band

        for i in range(len(it.by_income.brackets)):
            lower_threshold = it.by_income.brackets[i].threshold
            upper_threshold = it.by_income.brackets[i + 1].threshold if i < len(it.by_income.brackets) - 1 else np.inf
            self.comparisons += [(
                f"income_tax_by_income_{i}",
                self.sim.map_to(income_tax * (total_income >= lower_threshold) * (total_income < upper_threshold), "household"),
                it.by_income.brackets[i].amount,
            )]

        # Taxpayers by country and income band

        tax_band = self.sim.calc("tax_band", period=self.year).values
        tax_band = np.select([
            tax_band == "STARTER",
            tax_band == "INTERMEDIATE",
            True,
        ], [
            "BASIC",
            "BASIC",
            tax_band,
        ])

        for country in ("ENGLAND", "WALES", "NORTHERN_IRELAND", "SCOTLAND"):
            for band in ("BASIC", "HIGHER", "ADDITIONAL"):
                self.comparisons += [(
                    f"income_tax_payers_{country}_{band}",
                    self.sim.map_to(income_tax * (countries == country) * (tax_band == band), "household"),
                    it.payers._children[country]._children[band],
                )]
    
    def get_loss_subcomponents(self, household_weights: tf.Tensor) -> Iterable[Tuple]:
        for name, values, actual in self.comparisons:
            yield name, tf.reduce_sum(values * household_weights), actual
        