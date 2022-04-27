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

        for country in ("ENGLAND", "WALES", "NORTHERN_IRELAND", "SCOTLAND"):
            self.comparisons += [
                f"income_tax_{country}",
                household_income_tax * (countries == country),
                it._children[country]
            ]
        
        self.comparisons += [
            "income_tax_UNITED_KINGDOM",
            household_income_tax,
            it._children["UNITED_KINGDOM"]
        ]
    
    def get_loss_subcomponents(self, household_weights: tf.Tensor) -> Iterable[Tuple]:
        for name, values, actual in self.country_level_totals:
            yield name, tf.reduce_sum(values * household_weights), actual
        