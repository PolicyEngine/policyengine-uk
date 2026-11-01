from policyengine_uk.model_api import *
from policyengine_uk.programs import (
    budget_variables,
    budget_variables_in_effect,
    uprated_benefit_variables,
)

# The terms flagged `budget: benefit` in programs.yaml, in its budget_order.
HOUSEHOLD_BENEFIT_VARIABLES = budget_variables("benefit")


class household_benefits(Variable):
    value_type = float
    entity = Household
    label = "household benefits"
    documentation = (
        "Total value of benefits received by household: the programs.yaml "
        "terms flagged budget: benefit, less any whose budget_dropped_when "
        "parameter is true, plus the gov.contrib.benefit_uprating rates "
        "times the terms each rate scales (budget_uprating)."
    )
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        p = parameters(period)
        uprating = p.gov.contrib.benefit_uprating
        benefits = budget_variables_in_effect("benefit", p)
        general_benefits = add(
            household, period, uprated_benefit_variables(benefits, "all")
        )
        non_sp_benefits = add(
            household, period, uprated_benefit_variables(benefits, "non_sp")
        )
        return (
            add(household, period, benefits)
            + general_benefits * uprating.all
            + non_sp_benefits * uprating.non_sp
        )
