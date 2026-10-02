from policyengine_uk.model_api import *


def income_related_jsa_award(benunit, period, reported_award):
    """Income-based JSA paid on a reported award: the award less tariff
    income from capital, or nothing if the scheme is not active or the
    benefit unit fails the capital or remunerative work tests
    (jsa_income_eligible)."""
    JSA = benunit.simulation.tax_benefit_system.parameters(period).gov.dwp.JSA
    if not JSA.income.active:
        return benunit.empty_array()
    tariff_income = benunit("jsa_income_tariff_income", period)
    eligible = benunit("jsa_income_eligible", period)
    return where(eligible, max_(0, reported_award - tariff_income), 0)


class jsa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "JSA (income-based)"
    documentation = (
        "Reported income-based JSA screened through bounded capital and "
        "remunerative work tests (jsa_income_eligible). "
        "This is not a full entitlement model."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        if not parameters(period).gov.dwp.JSA.income.active:
            return benunit.empty_array()
        reported_award = add(benunit, period, ["jsa_income_reported"])
        return income_related_jsa_award(benunit, period, reported_award)
