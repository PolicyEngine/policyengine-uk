from policyengine_core.model_api import *


def disable_simulated_benefits(parameters, period):
    if parameters(period).gov.contrib.policyengine.disable_simulated_benefits:

        class DisableSimulatedBenefits(Reform):
            def apply(self):
                simulation = self.simulation

                BENEFITS = [
                    "afcs",
                    "attendance_allowance",
                    "bsp",
                    "carers_allowance",
                    "child_benefit",
                    "child_tax_credit",
                    "council_tax_benefit",
                    "dla_m",
                    "dla_sc",
                    "esa_contrib",
                    "esa_income",
                    "housing_benefit",
                    "iidb",
                    "incapacity_benefit",
                    "income_support",
                    "jsa_contrib",
                    "jsa_income",
                    "pension_credit",
                    "pip_dl",
                    "pip_m",
                    "sda",
                    "ssmg",
                    "state_pension",
                    "universal_credit",
                    "winter_fuel_allowance",
                    "working_tax_credit",
                ]
                time_period = simulation.dataset.time_period
                YEARS_IN_FUTURE = 10
                for variable in BENEFITS:
                    entity = simulation.tax_benefit_system.variables[
                        variable
                    ].entity.key
                    reported_value = simulation.calculate(
                        variable + "_reported", time_period, map_to=entity
                    )
                    for year in range(
                        time_period, time_period + YEARS_IN_FUTURE
                    ):
                        simulation.set_input(variable, year, reported_value)

                    if variable in ["child_tax_credit", "working_tax_credit"]:
                        # CTC and WTC have their own pre_minimum variables because tax credits aren't paid if
                        # below a threshold.
                        variable = variable + "_pre_minimum"
                        for year in range(
                            time_period, time_period + YEARS_IN_FUTURE
                        ):
                            simulation.set_input(
                                variable, year, reported_value
                            )

        return DisableSimulatedBenefits
