from policyengine_uk.model_api import *


def income_related_esa_award(benunit, period, reported_award):
    """Income-related ESA paid on a reported award: the award less tariff
    income from capital, or nothing if the benefit unit fails the capital
    or remunerative work tests (esa_income_eligible)."""
    tariff_income = benunit("esa_income_tariff_income", period)
    eligible = benunit("esa_income_eligible", period)
    return where(eligible, max_(0, reported_award - tariff_income), 0)


class esa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "ESA (income-based)"
    documentation = (
        "Reported income-related ESA screened through bounded capital and "
        "remunerative work tests (esa_income_eligible). "
        "This is not a full entitlement model."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        reported_award = add(benunit, period, ["esa_income_reported"])
        return income_related_esa_award(benunit, period, reported_award)
