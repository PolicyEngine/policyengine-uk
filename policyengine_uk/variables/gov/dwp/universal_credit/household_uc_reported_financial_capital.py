from policyengine_uk.model_api import *


class household_uc_reported_financial_capital(Variable):
    value_type = float
    entity = Household
    label = "Household UC capital reports consumed from the financial pool"
    documentation = (
        "Amounts consumed from the household financial proxy, counted once "
        "per benefit unit: a nonnegative complete uc_reported_capital override "
        "takes precedence over benunit_reported_capital. Without an override, "
        "use the nonnegative financial observation. Subtracting a complete "
        "override retains the inherited residual-pool convention; it does "
        "not imply that the override's asset composition is observed."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        person = household.members
        financial_capital = person.benunit("benunit_reported_capital", period)
        complete_override = person.benunit("uc_reported_capital", period)
        consumed_capital = where(
            complete_override >= 0, complete_override, financial_capital
        )
        return household.sum(
            max_(0, consumed_capital) * person("is_benunit_head", period)
        )
