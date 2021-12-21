from openfisca_uk.model_api import *


class baseline_hbai_excluded_income(Variable):
    label = "HBAI-excluded income (baseline)"
    documentation = "Total value of income not included in HBAI household net income in the baseline"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        # Establish if currently running a microsimulation
        if len(household.nb_persons()) > 1_000:
            from openfisca_uk import Microsimulation

            # Simulate baseline policy
            result = Microsimulation().simulation.calculate(
                "hbai_excluded_income", period
            )
            # Check that the dataset/year combination is valid
            # (i.e. that the arrays are the same size)
            if len(result) == len(household.nb_persons()):
                return result
        # If baseline policy not viable from the above method,
        # no change in HBAI excluded income
        return household("hbai_excluded_income", period)


class hbai_excluded_income(Variable):
    label = "HBAI-excluded income"
    documentation = (
        "Total value of income not included in HBAI household net income"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        return -add(
            household,
            period,
            [
                "expected_sdlt",
                "expected_ltt",
                "expected_lbtt",
            ],
        )


class hbai_excluded_income_change(Variable):
    label = "Change in HBAI-excluded income"
    documentation = "Effect of policy reforms on HBAI-excluded income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        return household("hbai_excluded_income", period) - household(
            "baseline_hbai_excluded_income", period
        )
