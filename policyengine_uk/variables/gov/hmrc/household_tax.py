from policyengine_uk.model_api import *
from policyengine_uk.programs import budget_variables, budget_variables_in_effect

# The terms flagged `budget: tax` in programs.yaml, in its budget_order.
HOUSEHOLD_TAX_VARIABLES = budget_variables("tax")


class household_tax(Variable):
    value_type = float
    entity = Household
    label = "household taxes"
    documentation = (
        "Total taxes owed by the household: the programs.yaml terms flagged "
        "budget: tax, less any whose budget_dropped_when parameter is true."
    )
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        taxes = budget_variables_in_effect("tax", parameters(period))
        return add(household, period, taxes)
