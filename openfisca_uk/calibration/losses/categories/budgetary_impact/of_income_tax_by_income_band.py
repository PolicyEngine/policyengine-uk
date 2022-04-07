import numpy as np
from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import parameters


class BudgetaryImpactOfIncomeTaxByIncomeBand(LossCategory):
    label = "Income tax revenue by income"
    parameter_folder = (
        parameters.calibration.budgetary_impact.of_income_tax_by_income_band
    )
    weight = 1 / 30

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        brackets = (
            BudgetaryImpactOfIncomeTaxByIncomeBand.parameter_folder.brackets
        )  # Last-3 brackets are impossible due to FRS non-capture
        num_thresholds = len(brackets)
        instant_str = f"{year}-01-01"
        for i in range(num_thresholds):
            lower_threshold = brackets[i].threshold(instant_str)
            upper_threshold = (
                brackets[i + 1].threshold(instant_str)
                if i < num_thresholds - 1
                else np.inf
            )
            income = sim.calc("total_income", period=year).values
            person_in_range = (income >= lower_threshold) & (
                income < upper_threshold
            )
            income_tax_in_range = (
                sim.calc("income_tax", period=year).values * person_in_range
            )
            household_income_tax = sim.map_to(
                income_tax_in_range, "person", "household"
            )
            aggregate = tf.reduce_sum(household_weights * household_income_tax)
            target = brackets[i].amount(instant_str)
            if person_in_range.sum() > 0:
                # If the FRS does not have any observations, skip the target.
                yield brackets[i].name + "." + str(year), aggregate, target

    def get_metrics():
        return BudgetaryImpactOfIncomeTaxByIncomeBand.parameter_folder.brackets

    def get_metric_names():
        return [
            bracket.name + "." + str(year)
            for bracket in BudgetaryImpactOfIncomeTaxByIncomeBand.parameter_folder.brackets
            for year in range(2019, 2027)
        ]
