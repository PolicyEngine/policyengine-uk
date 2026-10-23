from policyengine_uk.model_api import *


def income_related_esa_award(benunit, period, reported_award):
    """Income-related ESA paid on a reported award: the award less tariff
    income from capital, or nothing if the benefit unit fails the screen in
    esa_income_eligible."""
    tariff_income = benunit("esa_income_tariff_income", period)
    eligible = benunit("esa_income_eligible", period)
    return where(eligible, max_(0, reported_award - tariff_income), 0)


class esa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "ESA (income-based)"
    documentation = (
        "Reported income-related ESA screened through bounded capital and "
        "remunerative work tests (esa_income_eligible). Reports whose award "
        "has ended are left out (esa_income_report_closed): the owner's "
        "legacy benefits have closed, or the owner is the claimant or "
        "partner of a family that claims Universal Credit. "
        "This is not a full entitlement model."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        person = benunit.members
        reported_award = benunit.sum(
            person("esa_income_reported", period)
            * ~person("esa_income_report_closed", period)
        )
        return income_related_esa_award(benunit, period, reported_award)
