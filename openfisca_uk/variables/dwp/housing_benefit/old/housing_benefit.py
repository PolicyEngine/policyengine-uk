from openfisca_uk.model_api import *


class housing_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        rent = benunit("benunit_rent", period)
        LHA = benunit("LHA_eligible", period.this_year)
        applicable_amount = benunit(
            "housing_benefit_applicable_amount", period
        )
        income = benunit("housing_benefit_applicable_income", period)
        withdrawal_rate = parameters(
            period
        ).dwp.housing_benefit.means_test.withdrawal_rate
        final_amount = max_(
            0, rent - max_(0, income - applicable_amount) * withdrawal_rate
        )
        amount = where(
            LHA, min_(final_amount, benunit("LHA_cap", period)), final_amount
        )
        CAPPED_BENUNIT_BENEFITS = [
            "child_benefit",
            "child_tax_credit",
            "JSA_income",
            "income_support",
            "ESA_income",
        ]
        capped_benunit_benefits = add(benunit, period, CAPPED_BENUNIT_BENEFITS)
        CAPPED_PERSONAL_BENEFITS = [
            "JSA_contrib",
            "incapacity_benefit",
            "ESA_contrib",
            "SDA",
        ]
        capped_personal_benefits = aggr(
            benunit, period, CAPPED_PERSONAL_BENEFITS
        )
        other_capped_benefits = (
            capped_benunit_benefits + capped_personal_benefits
        )
        amount = max_(0, amount - benunit("hb_non_dep_deductions", period))
        final_amount = min_(
            amount * benunit("would_claim_hb", period),
            benunit("benefit_cap", period) - other_capped_benefits,
        )
        return max_(0, final_amount)
