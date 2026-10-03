from policyengine_uk.model_api import *


class legacy_benefits_closed(Variable):
    value_type = bool
    entity = BenUnit
    label = "Legacy benefits closed"
    documentation = (
        "Whether a legacy means-tested benefit this working-age family "
        "reports has closed: tax credits from 6 April 2025, and Income "
        "Support and income-based Jobseeker's Allowance from 1 April 2026 "
        "(their active parameters). DWP moved these families off legacy "
        "benefits with a migration notice covering all their legacy awards, "
        "so once one closes they all end: on a Universal Credit claim, or at "
        "the notice's deadline if the family does not claim. Housing Benefit "
        "and income-related Employment and Support Allowance join this list "
        "when the model ends their working-age awards. Families on the "
        "pension-age route are not moved to Universal Credit."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/44",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/46",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/33",
        "https://www.legislation.gov.uk/uksi/2025/1148/article/3A",
    )

    def formula(benunit, period, parameters):
        dwp = parameters(period).gov.dwp

        def reports(*variables):
            return add(benunit, period, list(variables)) > 0

        tax_credits_closed = reports(
            "child_tax_credit_reported", "working_tax_credit_reported"
        ) & (not dwp.tax_credits.active)
        income_support_closed = reports("income_support_reported") & (
            not dwp.income_support.active
        )
        jsa_income_closed = reports("jsa_income_reported") & (not dwp.JSA.income.active)
        # The transitional rules terminating legacy awards on a Universal
        # Credit claim do not apply to a claimant, or both joint claimants,
        # over the qualifying age for State Pension Credit (SI 2014/1230
        # reg 8(2B)); those families move to Pension Credit instead.
        pension_route = benunit("meets_pension_credit_age_conditions", period)
        return (
            tax_credits_closed | income_support_closed | jsa_income_closed
        ) & ~pension_route
