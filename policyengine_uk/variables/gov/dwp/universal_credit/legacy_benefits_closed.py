from policyengine_uk.model_api import *


def legacy_award_is_closed(reports, pension_age_route, mixed_age_couple, dwp):
    """Existing annual migration proxy for one award's owners.

    This preserves the model's programme closure dates and Pension Credit
    exceptions. It does not simulate notices, deadlines or run-on periods.
    """
    on_pension_credit = reports("pension_credit_reported")
    # A tax credit closure notice sent to Pension Credit, not Universal
    # Credit, a family on Pension Credit, or one on Child Tax Credit but
    # not Working Tax Credit that meets the Pension Credit age conditions
    # (single, both pension age, or a protected mixed-age couple; SI
    # 2019/167 art. 3A(1)). Every other tax credit family, including a
    # pension-age one on Working Tax Credit (SI 2014/1230 reg 60A), got a
    # Universal Credit migration notice (reg 44).
    pension_credit_route = on_pension_credit | (
        pension_age_route & ~reports("working_tax_credit_reported")
    )
    tax_credits_closed = (
        reports("child_tax_credit_reported", "working_tax_credit_reported")
        & (not dwp.tax_credits.active)
        & ~pension_credit_route
    )
    # Income Support and income-based JSA are working-age benefits; the
    # rules ending legacy awards on a Universal Credit claim do not apply
    # to a single claimant, or joint claimants both, over the qualifying
    # age for State Pension Credit (reg 8(2B)).
    wholly_pension_age = pension_age_route & ~mixed_age_couple
    income_support_closed = reports("income_support_reported") & (
        not dwp.income_support.active
    )
    jsa_income_closed = reports("jsa_income_reported") & (not dwp.JSA.income.active)
    return tax_credits_closed | (
        (income_support_closed | jsa_income_closed)
        & ~on_pension_credit
        & ~wholly_pension_age
    )


class legacy_benefits_closed(Variable):
    value_type = bool
    entity = BenUnit
    label = "Moved off legacy benefits onto the Universal Credit route"
    documentation = (
        "Annual proxy for whether DWP has moved the claimant and partner off "
        "their legacy means-tested "
        "benefits towards Universal Credit because one they report has closed: "
        "tax credits from 6 April 2025, and Income Support and income-based "
        "Jobseeker's Allowance from 1 April 2026 (their active parameters). "
        "The migration notice covers all the family's legacy awards, so they "
        "all end: on a Universal Credit claim, or at the notice's deadline if "
        "the family does not claim. Families DWP sent to Pension Credit "
        "instead are excluded: those on Pension Credit, and those on Child Tax "
        "Credit but not Working Tax Credit that meet the Pension Credit age "
        "conditions. Pension-age and protected mixed-age families on Working "
        "Tax Credit are included; Income Support and income-based JSA "
        "closures do not move a wholly pension-age family. Housing Benefit and income-related "
        "Employment and Support Allowance join this list when the model ends "
        "their working-age awards. Reports by other benefit-unit members do "
        "not close or shield this award. This annual proxy does not model "
        "actual notices, deadlines, run-on periods or Housing Benefit exceptions."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/44",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/46",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/60A",
        "https://www.legislation.gov.uk/uksi/2019/167/article/3A",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/33",
        "https://www.legislation.gov.uk/uksi/2025/1148/article/3A",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        owners = person("is_claimant_or_partner", period)

        def reports(*variables):
            amounts = sum(person(name, period) for name in variables)
            return benunit.sum(amounts * owners) > 0

        return legacy_award_is_closed(
            reports,
            benunit("meets_pension_credit_age_conditions", period),
            benunit("is_mixed_age_couple", period),
            parameters(period).gov.dwp,
        )
