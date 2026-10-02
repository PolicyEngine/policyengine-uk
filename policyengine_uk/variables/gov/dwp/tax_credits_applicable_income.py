from policyengine_uk.model_api import *

# The branch in which tax credits are paid without the income test.
PENSION_CREDIT_PASSPORT_BRANCH = "tax_credits_pension_credit_passport"


def pension_credit_with_passported_tax_credits(benunit, period, parameters):
    """Pension Credit payable alongside tax credits paid without the income test.

    Working tax credit is Pension Credit income (SPCA 2002 s.15(1)(b)), so
    Pension Credit depends on the tax credit award, and TCA 2002 s.7(2) makes
    the award depend on Pension Credit. The passport is consistent when
    Pension Credit stays payable once the passported award is counted. This
    calculates Pension Credit in a branch in which the income test is lifted:
    where it is payable there, the passport holds, and the simulation's own
    award and Pension Credit then equal the branch's.

    Where Pension Credit is payable only on the income-tested award, no
    consistent state exists: lifting the test would end Pension Credit, which
    would restore the test. The income test then stays, with the Pension
    Credit calculated on that award.

    In years with no tax credit awards, working tax credit is nil whether or
    not the test applies, so Pension Credit is read directly.
    """
    if not parameters(period).gov.dwp.tax_credits.active:
        return benunit("pension_credit", period)
    simulation = benunit.simulation
    branch = simulation.get_branch(PENSION_CREDIT_PASSPORT_BRANCH)
    try:
        branch.set_input("tax_credits_applicable_income", period, benunit.empty_array())
        return branch.calculate("pension_credit", period)
    finally:
        simulation.branches.pop(PENSION_CREDIT_PASSPORT_BRANCH, None)


class tax_credits_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable income for Tax Credits"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/2006/regulation/3",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/7",
        "https://www.legislation.gov.uk/uksi/2002/2008/regulation/4",
    )

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant and partner and, as the model did
        # before, the programme's own children or young persons. The regulations count
        # only the claimant's and partner's (TCA 2002 s.7); dropping dependants' own
        # income is a follow-up. Anyone else in the benefit unit does not count.
        person = benunit.members
        members = person("is_claimant_or_partner", period) | person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        TC = parameters(period).gov.dwp.tax_credits
        STEP_1_COMPONENTS = [
            "private_pension_income",
            "savings_interest_income",
            "dividend_income",
            "property_income",
        ]
        income = add_for_members(benunit, period, STEP_1_COMPONENTS, members)
        income = max_(income - TC.means_test.non_earned_disregard, 0)
        STEP_2_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "social_security_income",
            "miscellaneous_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            STEP_2_COMPONENTS.append("basic_income")
        income += add_for_members(benunit, period, STEP_2_COMPONENTS, members)
        # TCA 2002 s.7(2) and SI 2002/2008 reg 4(1): no income test while "the
        # person, or either of the persons" claiming is entitled to Income
        # Support, income-based JSA or income-related ESA. That is the claimant's
        # or partner's award, not another member's. The reg 4(1)(a) exception,
        # Income Support due only under IS Regs 1987 reg 6(2) and (3) (the
        # lone parent run-on), has no effect: those paragraphs were omitted
        # from 25 October 2004 (SI 2003/1589 reg 2(a)(i)). Reg 4(2), which
        # keeps the test for working tax credit in the four-week run-on of
        # WTC Regs 2002 reg 7D, is not modelled: a whole-year award has no
        # run-on period.
        EXEMPT_BENEFITS = [
            "income_support",
            "claimant_or_partner_esa_income",
            "claimant_or_partner_jsa_income",
        ]
        on_exempt_benefits = (
            add_for_members(benunit, period, EXEMPT_BENEFITS, members) > 0
        )
        # Reg 4(1)(d): State Pension Credit, which is the guarantee credit,
        # the savings credit or both (SPCA 2002 s.1(3)). A Pension Credit
        # award covers the claimant and any partner.
        if TC.means_test.pension_credit_passport:
            on_exempt_benefits = on_exempt_benefits | (
                pension_credit_with_passported_tax_credits(benunit, period, parameters)
                > 0
            )
        return income * ~on_exempt_benefits
