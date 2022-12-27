from policyengine_uk.data.datasets import EnhancedFRS, SynthFRS
from policyengine_uk.model_api import *


class poverty_line(Variable):
    label = "poverty line"
    documentation = "The line below which a household is in poverty."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        equivalisation = household("household_equivalisation_bhc", period)
        return (
            parameters(period).household.poverty.absolute_poverty_threshold_bhc
            * WEEKS_IN_YEAR
            * equivalisation
        )


class deep_poverty_line(Variable):
    label = "deep poverty line"
    documentation = "The line below which a household is in deep poverty."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return household("poverty_line", period) / 2


class poverty_gap(Variable):
    label = "poverty gap"
    documentation = "The financial gap between net household income and the poverty line (before housing costs)."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        income = household("hbai_household_net_income", period)
        line = household("poverty_line", period)
        return max_(0, line - income)


class deep_poverty_gap(Variable):
    label = "deep poverty gap"
    documentation = "The financial gap between net household income and the deep poverty line (before housing costs)."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        income = household("hbai_household_net_income", period)
        line = household("deep_poverty_line", period)
        return max_(0, line - income)


class in_poverty(Variable):
    label = "in poverty"
    documentation = (
        "Whether the household is in absolute poverty (before housing costs)."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period, parameters):
        return household("poverty_gap", period) > 0


class in_deep_poverty(Variable):
    label = "in deep poverty"
    documentation = "Whether the household is in deep absolute poverty (below half the poverty line, before housing costs)."
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period, parameters):
        return household("deep_poverty_gap", period) > 0


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
    unit = GBP

    def formula(household, period, parameters):
        return (
            parameters(period).household.poverty.absolute_poverty_threshold_bhc
            * WEEKS_IN_YEAR
        )


class in_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in absolute poverty, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income_ahc", period)
        threshold = parameters(
            period
        ).household.poverty.absolute_poverty_threshold_ahc
        return income < (threshold * WEEKS_IN_YEAR)


class in_deep_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in deep absolute poverty (below half the poverty line), before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income", period)
        threshold = parameters(
            period
        ).household.poverty.absolute_poverty_threshold_bhc
        return income < (threshold * WEEKS_IN_YEAR / 2)


class in_deep_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in deep absolute poverty (below half the poverty line), after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income_ahc", period)
        threshold = parameters(
            period
        ).household.poverty.absolute_poverty_threshold_ahc
        return income < (threshold * WEEKS_IN_YEAR / 2)


class poverty_line_bhc(Variable):
    value_type = float
    entity = Household
    label = "The poverty line for the household, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        threshold = parameters(
            period
        ).household.poverty.absolute_poverty_threshold_bhc
        equivalisation = household("household_equivalisation_bhc", period)
        return threshold * equivalisation * WEEKS_IN_YEAR


class poverty_line_ahc(Variable):
    value_type = float
    entity = Household
    label = "The poverty line for the household, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        threshold = parameters(
            period
        ).household.poverty.absolute_poverty_threshold_ahc
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
    unit = GBP

    def formula(household, period, parameters):
        if not parameters(period).household.poverty.exclude_non_hbai_income:
            return 0
        # Establish if currently running a microsimulation
        if len(household.nb_persons()) > 1_000:
            from policyengine_uk import Microsimulation

            # Simulate baseline policy
            dataset = EnhancedFRS if 2022 in EnhancedFRS.years else SynthFRS
            result = Microsimulation(
                dataset=dataset, dataset_year=2022
            ).calculate("hbai_excluded_income", period)
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
    unit = GBP

    def formula(household, period, parameters):
        VARIABLES = [
            "corporate_tax_incidence",
        ]
        return -add(household, period, VARIABLES)


class hbai_excluded_income_change(Variable):
    label = "Change in HBAI-excluded income"
    documentation = "Effect of policy reforms on HBAI-excluded income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        hbai_excluded_income = household("hbai_excluded_income", period)
        baseline_hbai_excluded_income = household(
            "baseline_hbai_excluded_income", period
        )
        return hbai_excluded_income - baseline_hbai_excluded_income
