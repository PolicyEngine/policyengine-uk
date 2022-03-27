from openfisca_uk_data.datasets import FRSEnhanced, SynthFRS
from openfisca_uk.model_api import *


class in_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = (
        "Whether the household is in absolute poverty, before housing costs"
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income", period)
        return income < household("poverty_threshold_bhc", period)


class poverty_threshold_bhc(Variable):
    label = "Poverty threshold (BHC)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        return (
            parameters(period).poverty.absolute_poverty_threshold_bhc
            * WEEKS_IN_YEAR
        )


class in_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in absolute poverty, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income_ahc", period)
        threshold = parameters(period).poverty.absolute_poverty_threshold_ahc
        return income < (threshold * WEEKS_IN_YEAR)


class in_deep_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in deep absolute poverty (below half the poverty line), before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income", period)
        threshold = parameters(period).poverty.absolute_poverty_threshold_bhc
        return income < (threshold * WEEKS_IN_YEAR / 2)


class in_deep_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in deep absolute poverty (below half the poverty line), after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income_ahc", period)
        threshold = parameters(period).poverty.absolute_poverty_threshold_ahc
        return income < (threshold * WEEKS_IN_YEAR / 2)


class poverty_line_bhc(Variable):
    value_type = float
    entity = Household
    label = "The poverty line for the household, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        threshold = parameters(period).poverty.absolute_poverty_threshold_bhc
        equivalisation = household("household_equivalisation_bhc", period)
        return threshold * equivalisation * WEEKS_IN_YEAR


class poverty_line_ahc(Variable):
    value_type = float
    entity = Household
    label = "The poverty line for the household, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        threshold = parameters(period).poverty.absolute_poverty_threshold_ahc
        equivalisation = household("household_equivalisation_ahc", period)
        return threshold * equivalisation * WEEKS_IN_YEAR


class poverty_gap_bhc(Variable):
    value_type = float
    entity = Household
    label = "Positive financial gap between net household income and the poverty line"
    definition_period = YEAR

    def formula(household, period, parameters):
        net_income = household("hbai_household_net_income", period)
        return max_(0, household("poverty_line_bhc", period) - net_income)


class poverty_gap_ahc(Variable):
    value_type = float
    entity = Household
    label = "Positive financial gap between net household income and the poverty line, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        net_income = household("hbai_household_net_income_ahc", period)
        return max_(0, household("poverty_line_ahc", period) - net_income)


class baseline_hbai_excluded_income(Variable):
    label = "HBAI-excluded income (baseline)"
    documentation = "Total value of income not included in HBAI household net income in the baseline"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        if not parameters(period).poverty.exclude_non_hbai_income:
            return 0
        # Establish if currently running a microsimulation
        if len(household.nb_persons()) > 1_000:
            from openfisca_uk import Microsimulation

            # Simulate baseline policy
            dataset = FRSEnhanced if 2019 in FRSEnhanced.years else SynthFRS
            result = Microsimulation(
                dataset=dataset, year=2019
            ).simulation.calculate("hbai_excluded_income", period)
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
        VARIABLES = [
            "expected_sdlt",
            "expected_ltt",
            "expected_lbtt",
            "business_rates",
        ]
        return -add(household, period, VARIABLES)


class hbai_excluded_income_change(Variable):
    label = "Change in HBAI-excluded income"
    documentation = "Effect of policy reforms on HBAI-excluded income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        hbai_excluded_income = household("hbai_excluded_income", period)
        baseline_hbai_excluded_income = household(
            "baseline_hbai_excluded_income", period
        )
        return hbai_excluded_income - baseline_hbai_excluded_income
