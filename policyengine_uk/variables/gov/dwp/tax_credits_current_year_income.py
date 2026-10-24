from policyengine_uk.model_api import *

# Step one of SI 2002/2006 reg 3(1): pension income (reg 5), investment income
# (reg 10), property income (reg 11), foreign income (reg 12) and notional
# income (reg 13). Pension income includes "any pension to which section 577
# ... of ITEPA applies" (reg 5(1)(a)), and ITEPA 2003 s.577(1) applies to "the
# state pension" and "widowed parent's allowance", so both are step one, with
# the £300 disregard.
# private_pension_income is pension income (reg 5(1)(b), (d): ITEPA ss.569,
# 579A) or, for a foreign pension, foreign income (reg 12), which is also step
# one. savings_interest_income and dividend_income are investment income (reg
# 10(1)(a), (d)), and property_income_after_finance_costs retains the
# model's deduction of property finance costs.
STEP_ONE_INCOME = [
    "state_pension",
    "widowed_parents_allowance",
    "private_pension_income",
    "savings_interest_income",
    "dividend_income",
    "property_income_after_finance_costs",
]

# Social security income (reg 7): benefits payable under the Contributions and
# Benefits Act, the Jobseekers Act 1995 and Part 1 of the Welfare Reform Act
# 2007 (reg 7(1)(a)), and amounts under regulations made under s.28 of the
# Social Security (Scotland) Act 2018 (reg 7(1)(ab), from 15 March 2023):
# Carer Support Payment and the Scottish Carer Supplement component. It is the
# model's social_security_income without the State Pension and Widowed
# Parent's Allowance (SSCBA 1992 s.39A): "Pensions under the Contributions and
# Benefits Act which are pension income by virtue of regulation 5(1)(a) are not
# social security income" (reg 7(2)). The model's
# other benefits are disregarded by reg 7(3) Table 3, or are not under an Act
# reg 7(1) lists (Pension Credit, Universal Credit). Two partial disregards
# are not modelled: short-term lower-rate Incapacity Benefit and Incapacity
# Benefit after Invalidity Benefit (item 14), and contribution-based JSA above
# the ITEPA s.674 taxable maximum (item 16).
SOCIAL_SECURITY_INCOME = [
    "incapacity_benefit",
    "jsa_contrib_reported",
    "esa_contrib_reported",
    "carers_allowance",
    "carer_support_payment",
    # SSI 2023/302 reg 14A: a component of support under the same s.28 rules.
    # It starts in 2026, after tax credit awards end.
    "scottish_carer_supplement",
]


class tax_credits_current_year_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Current year income for Tax Credits"
    documentation = (
        "The claimant's, or joint claimants', income for the tax year "
        "(TCA 2002 s.7(4); SI 2002/2006 reg 3), before TCA 2002 s.7(2) lifts "
        "the income test for a claimant on a prescribed benefit. The model "
        "takes it as the relevant income (s.7(3)). The income test reads "
        "tax_credits_applicable_income, which is nil while the test is "
        "lifted; the targeted childcare criteria read this gross figure."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/21/section/7",
        "https://www.legislation.gov.uk/uksi/2002/2006/regulation/3",
        "https://www.legislation.gov.uk/uksi/2002/2006/regulation/5",
        "https://www.legislation.gov.uk/uksi/2002/2006/regulation/7",
        "https://www.legislation.gov.uk/ukpga/2003/1/section/577",
    )

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant or, on a joint claim, the
        # claimants (TCA 2002 s.7; Tax Credits (Definition and Calculation of
        # Income) Regs 2002 reg 3(1)). A child's or qualifying young person's
        # own income does not count, nor anyone else's in the benefit unit.
        person = benunit.members
        members = person("is_claimant_or_partner", period)
        TC = parameters(period).gov.dwp.tax_credits
        income = add_for_members(benunit, period, STEP_ONE_INCOME, members)
        # "If the result of this step is £300 or less, it is treated as nil. If
        # the result of this step is more than £300, only the excess is taken
        # into account in the following steps." The £300 is per claim, not per
        # joint claimant.
        income = max_(income - TC.means_test.non_earned_disregard, 0)
        # Step two: employment income (reg 4), social security income (reg 7)
        # and miscellaneous income (reg 18). Trading income is step four, which
        # adds it to the same total.
        STEP_2_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            *SOCIAL_SECURITY_INCOME,
            "miscellaneous_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            STEP_2_COMPONENTS.append("basic_income")
        income += add_for_members(benunit, period, STEP_2_COMPONENTS, members)
        # SI 2002/2006 reg 3(1) Step Four: only the claimants' losses
        # reduce their joint income; a child's loss is not theirs.
        claimants = person("is_claimant_or_partner", period)
        return max_(
            0, income - add_for_members(benunit, period, ["trading_loss"], claimants)
        )
