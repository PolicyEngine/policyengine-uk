from policyengine_uk.model_api import *


class jsa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "JSA (income-based)"
    documentation = (
        "Reported income-based JSA screened through a bounded capital test. "
        "This is not a full entitlement model."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        if not parameters(period).gov.dwp.JSA.income.active:
            return benunit.empty_array()
        reported_award = add(benunit, period, ["jsa_income_reported"])
        tariff_income = benunit("jsa_income_tariff_income", period)
        eligible = benunit("jsa_income_eligible", period)
        return where(eligible, max_(0, reported_award - tariff_income), 0)
