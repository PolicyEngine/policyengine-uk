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

    In law Pension Credit never rises with working tax credit: the guarantee
    credit falls by the whole of it (s.2(2)), and it is not qualifying income
    for the savings credit (SPC Regs 2002 reg 9(a)). So where Pension Credit
    is payable only on the income-tested award, no consistent state exists:
    lifting the test would end Pension Credit, which would restore the test.
    The income test then stays, with the Pension Credit calculated on that
    award. (The model's savings credit counts working tax credit as
    qualifying income, so it can rise with the award; where both states are
    then consistent, the passport is taken.)

    "Entitled" is read as payable: at income exactly equal to the minimum
    guarantee, where no savings credit is payable, a nil guarantee credit
    gives no passport.

    In years with no tax credit awards, working tax credit is nil whether or
    not the test applies, so Pension Credit is read directly.
    """
    if not parameters(period).gov.dwp.tax_credits.active:
        return benunit("pension_credit", period)
    simulation = benunit.simulation
    # get_branch returns an existing branch of that name, or this simulation
    # if it has that name, so take a name in use by neither.
    name = PENSION_CREDIT_PASSPORT_BRANCH
    while name in simulation.branches or name == simulation.branch_name:
        name += "_"
    branch = simulation.get_branch(name)
    try:
        branch.set_input("tax_credits_applicable_income", period, benunit.empty_array())
        # Through the population, so a microsimulation returns an
        # unweighted array.
        return branch.populations[benunit.entity.key]("pension_credit", period)
    finally:
        simulation.branches.pop(name, None)


class tax_credits_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable income for Tax Credits"
    documentation = (
        "The income the tax credit income test applies to: the current year "
        "income, or nil while the claimant or either joint claimant is "
        "entitled to a benefit prescribed for TCA 2002 s.7(2)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/21/section/7",
        "https://www.legislation.gov.uk/uksi/2002/2008/regulation/4",
    )

    def formula(benunit, period, parameters):
        income = benunit("tax_credits_current_year_income", period)
        # TCA 2002 s.7(2) and SI 2002/2008 reg 4(1): no income test while "the
        # person, or either of the persons" claiming is entitled to Income
        # Support, income-based JSA or income-related ESA. That is the claimant's
        # or partner's award, not another member's. The reg 4(1)(a) and (b)
        # exceptions, Income Support due only under IS Regs 1987 reg 6(2) and
        # (3) (the lone parent run-on, omitted in Great Britain from 25 October
        # 2004 by SI 2003/1589 reg 2(a)(i)) and the Northern Ireland
        # equivalent, have no effect: the model has no Income Support run-on.
        # Reg 4(2), which keeps the test for working tax credit in the
        # four-week run-on of WTC Regs 2002 reg 7D, is not modelled: a
        # whole-year award has no run-on period.
        EXEMPT_BENEFITS = [
            "income_support",
            "claimant_or_partner_esa_income",
            "claimant_or_partner_jsa_income",
        ]
        on_exempt_benefits = add(benunit, period, EXEMPT_BENEFITS) > 0
        # Reg 4(1)(d): State Pension Credit, which is the guarantee credit,
        # the savings credit or both (SPCA 2002 s.1(3)). A Pension Credit
        # award covers the claimant and any partner.
        if parameters(period).gov.dwp.tax_credits.means_test.pension_credit_passport:
            on_exempt_benefits = on_exempt_benefits | (
                pension_credit_with_passported_tax_credits(benunit, period, parameters)
                > 0
            )
        return income * ~on_exempt_benefits
