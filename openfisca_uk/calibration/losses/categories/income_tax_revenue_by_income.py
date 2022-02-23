import numpy as np
from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk.parameters import parameters


class IncomeTaxRevenueByIncome(LossCategory):
    weight = 1e3
    label = "Income tax revenue by income"
    parameter_folder = parameters.calibration.income_tax.revenue_by_income

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        brackets = IncomeTaxRevenueByIncome.parameter_folder.brackets
        num_thresholds = len(brackets)
        instant_str = f"{year}-01-01"
        for i in range(num_thresholds):
            lower_threshold = brackets[i].threshold(instant_str)
            upper_threshold = (
                brackets[i + 1].threshold(instant_str)
                if i < num_thresholds - 1
                else np.inf
            )
            income = sim.calc("total_income", period=year)
            person_in_range = (income >= lower_threshold) & (
                income < upper_threshold
            )
            income_tax_in_range = (
                sim.calc("income_tax", period=year) * person_in_range
            )
            household_income_tax = sim.map_to(
                income_tax_in_range, "person", "household"
            )
            aggregate = tf.reduce_sum(household_weights * household_income_tax)
            target = brackets[i].amount(instant_str)
            yield brackets[i].name + "." + str(year), aggregate, target
