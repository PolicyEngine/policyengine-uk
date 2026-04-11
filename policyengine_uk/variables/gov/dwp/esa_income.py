from policyengine_uk.model_api import *


class esa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "ESA (income-based)"
    documentation = (
        "Reported income-related ESA screened through a bounded capital test. "
        "This is not a full entitlement model."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        reported_award = add(benunit, period, ["esa_income_reported"])
        tariff_income = benunit("esa_income_tariff_income", period)
        eligible = benunit("esa_income_eligible", period)
        return where(eligible, max_(0, reported_award - tariff_income), 0)
