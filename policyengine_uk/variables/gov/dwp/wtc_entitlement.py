from policyengine_uk.model_api import *


class wtc_entitlement(Variable):
    label = "WTC entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "is_WTC_eligible"

    def formula(benunit, period, parameters):
        # With no awards in payment, return before reading the income test:
        # Pension Credit counts working tax credit (SPCA 2002 s.15(1)(b)), and
        # the tax credit income test reads Pension Credit directly in those
        # years (tax_credits_applicable_income).
        if not parameters(period).gov.dwp.tax_credits.active:
            return benunit.empty_array()
        return where(
            benunit("tax_credits", period) > 0,
            benunit("working_tax_credit_pre_minimum", period),
            0,
        )
