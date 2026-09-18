from policyengine_uk.model_api import *


class net_wealth(Variable):
    label = "Net wealth"
    documentation = (
        "Total wealth less mortgage, consumer, and student loan debt. Unlike "
        "total_wealth (gross assets), net wealth can be negative when a "
        "household's debts exceed its assets."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        total_wealth = household("total_wealth", period)
        mortgage_debt = household("mortgage_debt", period)
        consumer_debt = household("consumer_debt", period)
        student_loan_debt = add(household, period, ["student_loan_balance"])
        return total_wealth - mortgage_debt - consumer_debt - student_loan_debt
