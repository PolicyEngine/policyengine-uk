from policyengine_uk.model_api import *


class housing_benefit_pre_additional_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = (
        "Housing Benefit earnings disregard excluding the additional earnings amount"
    )
    documentation = "Ordinary/special/permitted-work and accommodation disregards before the additional earnings amount. This intermediate avoids a circular dependency with the earnings-limited childcare deduction. Savings-credit-only cases retain PC grounds, with only the permitted higher lone-parent/exempt-work modifications."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/27",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        earnings = benunit("housing_benefit_net_earnings", period)
        standard = benunit("housing_benefit_standard_earnings_disregard", period)
        accommodation = min_(
            max_(earnings - standard, 0),
            benunit(
                "housing_benefit_specified_or_temporary_accommodation_disregard", period
            ),
        )
        pc = benunit(
            "housing_benefit_pension_credit_earnings_disregard_assessment", period
        )
        lone = where(
            benunit("is_lone_parent", period),
            min_(earnings, p.lone_parent * WEEKS_IN_YEAR),
            0,
        )
        sc_only = benunit(
            "housing_benefit_pension_age_regulations_apply", period
        ) & benunit("in_receipt_of_savings_credit_only", period)
        sc_base = max_(
            pc, max_(lone, benunit("housing_benefit_permitted_work_disregard", period))
        )
        return where(sc_only, sc_base, standard + accommodation)
