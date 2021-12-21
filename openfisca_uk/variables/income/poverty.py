from openfisca_uk.model_api import *


class baseline_hbai_excluded_income(Variable):
    label = "HBAI-excluded income (baseline)"
    documentation = "Total value of income not included in HBAI household net income in the baseline"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        from openfisca_uk import Microsimulation

        return Microsimulation().simulation.calculate(
            "hbai_excluded_income", period
        )


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
        return add(
            household,
            period,
            [
                "expected_sdlt",
                "expected_ltt",
                "expected_lbtt",
            ],
        )
