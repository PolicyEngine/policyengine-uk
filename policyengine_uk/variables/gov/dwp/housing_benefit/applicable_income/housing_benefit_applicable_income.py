from policyengine_uk.model_api import *


def hb_income_before_deductions(benunit, period, parameters):
    """Ordinary income before childcare/disregards and the income floor."""
    # Members whose income counts: the claimant and partner (SSCBA 1992
    # s.136(1); HB Regs 2006 reg 25(1), HB (SPC) Regs 2006 reg 23(1)). "The
    # income and capital of a child or young person shall not be treated as
    # the income and capital of the claimant" (HB Regs 2006 reg 25(3)).
    # Pension-age reg 23(3) and NI regs 22(3) / 21(3) do the same.
    # Anyone else in the benefit unit does not count either.
    person = benunit.members
    members = person("is_claimant_or_partner", period)
    # Only the claimant's and partner's income-related awards: their income is
    # the claimant's (SSCBA s.136(1); HB Regs 2006 reg 25(1)). A member outside
    # the family who has an award of their own claims in their own right.
    # Income Support already needs the claimant's or partner's own award
    # (income_support_eligible).
    # Child Benefit is disregarded (GB Sch 5 para 65; NI Sch 6 para 64).
    # Pension-age exclusions: GB reg 29(1)(j)(vi); NI reg 27(1)(h)(v).
    BENUNIT_MEANS_TESTED_BENEFITS = [
        "income_support",
        "claimant_or_partner_jsa_income",
        "claimant_or_partner_esa_income",
    ]
    # Social Fund payments including SSMG are disregarded (GB Sch 5 para 31;
    # NI Sch 6 para 32); pension-age GB reg 29(1)(j)(ix) / NI reg 27(1)(h)(viii).
    PERSONAL_BENEFITS = [
        "carers_allowance",
        # The Carer Support Payment component only: the Scottish Carer
        # Supplement is disregarded (HB Regs 2006 Sch 5 para 75; HB (SPC)
        # Regs 2006 reg 29(1)(j)(xviiha)), so scottish_carer_supplement is
        # not listed.
        "carer_support_payment",
        "esa_contrib",
        "jsa_contrib",
        "state_pension",
        "maternity_allowance",
        # Statutory sick, maternity and paternity pay are earnings: SI
        # 2006/213 reg 35(1)(i); SI 2006/214 reg 35(1)(h) and (i); NI SR
        # 2006/405 reg 32(1)(i); NI SR 2006/406 reg 33(1)(h) and (i). The
        # income tax and National Insurance deducted below include the
        # tax on them (employment_benefits, ni_class_1_income).
        "statutory_sick_pay",
        "statutory_maternity_pay",
        "statutory_paternity_pay",
        # Counted by both regimes: HB (SPC) Regs 2006 reg 29(1)(j), whose
        # exceptions touching these are the IIDB increases under SSCBA
        # ss.104-105 (head (iii)) and non-partner dependant increases (head
        # (viii)); heads (iv) and (v) cover the Sch 8 schemes for old
        # industrial injury cases. And HB Regs 2006 reg 40 with Sch 5,
        # whose para 9 attendance allowance disregard covers the
        # ss.104-105 increases (reg 2(1)). iidb is the whole reported
        # payment and cannot separate those increases.
        "iidb",
        "sda",
        "incapacity_benefit",
    ]
    INCOME_COMPONENTS = [
        "employment_income",
        "self_employment_income",
        "property_income_after_finance_costs",
        "private_pension_income",
    ]
    bi = parameters(period).gov.contrib.ubi_center.basic_income
    # Add personal benefits, credits and total benefits to income
    benefits = add_for_members(benunit, period, BENUNIT_MEANS_TESTED_BENEFITS, members)
    income = add_for_members(benunit, period, INCOME_COMPONENTS, members)
    personal_benefits = add_for_members(benunit, period, PERSONAL_BENEFITS, members)
    credits = add_for_members(benunit, period, ["tax_credits"], members)
    # Maintenance paid to the claimant or partner by a spouse, civil partner
    # or former partner is income other than earnings (HB Regs 2006 reg 40(1);
    # HB (SPC) Regs 2006 reg 29(1)(o)), less £15 a week where the family
    # includes a child or young person. Child maintenance is disregarded in
    # full (HB Regs 2006 Sch 5 para 47A) or is not listed as income (reg
    # 29(1)), so maintenance_income is not counted.
    spousal_maintenance = benunit.sum(
        max_(0, person("spousal_maintenance_income", period)) * members
    ) - benunit("housing_benefit_maintenance_disregard", period)
    # Widowed parent's allowance less £15 a week (HB Regs 2006 Sch 5 para
    # 16(b); HB (SPC) Regs 2006 Sch 5 para 7), the claimant's and partner's
    # only.
    widowed_parents_allowance = benunit(
        "housing_benefit_widowed_parents_allowance_income", period
    )
    increased_income = (
        income
        + personal_benefits
        + credits
        + benefits
        + spousal_maintenance
        + widowed_parents_allowance
    )

    if not bi.interactions.include_in_means_tests:
        # Basic income is already in personal benefits, deduct if needed
        increased_income -= add_for_members(benunit, period, ["basic_income"], members)
    # Reduce increased income by pension contributions and tax
    p = parameters(period).gov.dwp.housing_benefit.means_test
    pension_contributions = (
        add_for_members(benunit, period, ["pension_contributions"], members)
        * p.pension_contribution_deduction_rate
    )
    TAX_COMPONENTS = [
        "income_tax_before_winter_fuel_payment_charge",
        "national_insurance",
    ]
    tax = add_for_members(benunit, period, TAX_COMPONENTS, members)
    increased_income_reduced_by_tax_and_pensions = (
        increased_income - tax - pension_contributions
    )
    tariff_income = benunit("housing_benefit_tariff_income", period)
    return increased_income_reduced_by_tax_and_pensions + tariff_income


class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "relevant income for Housing Benefit means test"
    documentation = (
        "Income taken into account in the Housing Benefit means test. It is "
        "nil for a family on Universal Credit, Income Support, income-based "
        "Jobseeker's Allowance or income-related Employment and Support "
        "Allowance (housing_benefit_on_passporting_benefit), whose whole "
        "income is disregarded, and for a pension-age family receiving a "
        "guarantee credit (the guarantee credit passport). Where the Pension "
        "Credit award is savings credit only, it is the Secretary of State's "
        "assessment of income plus the savings credit payable, less childcare "
        "charges and the earnings disregards. Otherwise it is the family's "
        "income under the Housing Benefit rules."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/25",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/65",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/31",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/23",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/29",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/22",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/6/paragraph/64",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/6/paragraph/32",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/21",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/27",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/4",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/6/paragraph/4",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/5",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/40",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/16",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/47",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/29",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/26",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/24",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/25",
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        income_before_deductions = hb_income_before_deductions(
            benunit, period, parameters
        )
        pension_age_regulations = benunit(
            "housing_benefit_pension_age_regulations_apply", period
        )
        disregard = benunit("housing_benefit_applicable_income_disregard", period)
        childcare_element = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        income_under_general_rules = max_(
            0,
            income_before_deductions - disregard - childcare_element,
        )
        # SI 2006/214 reg 27 (NI: SR 2006/406 reg 25): where the award of
        # Pension Credit is savings credit only, the Secretary of State's
        # assessment of income is used instead, plus the savings credit. That
        # regulation is in the pension-age regulations, so it applies only
        # where they do.
        savings_credit_only = pension_age_regulations & benunit(
            "in_receipt_of_savings_credit_only", period
        )
        applicable_income = where(
            savings_credit_only,
            benunit("housing_benefit_savings_credit_only_income", period),
            income_under_general_rules,
        )
        # Guarantee Credit passport: SI 2006/214 reg 26 (NI: SR 2006/406
        # reg 24) disregards the whole of the capital and income of a
        # claimant in receipt, or whose partner is in receipt, of a
        # guarantee credit. By reg 2(5), receipt includes awards withheld
        # solely under SPC Regs 2002 reg 13 (small amounts), which the
        # model does not withhold. Entitlement without a claim is not receipt.
        passported = pension_age_regulations & benunit(
            "in_receipt_of_guarantee_credit", period
        )
        # SI 2006/213 Sch 5 para 4 (NI: SR 2006/405 Sch 6 para 4) disregards
        # "the whole of his income" where a claimant is on universal credit,
        # income support, an income-based jobseeker's allowance or an
        # income-related employment and support allowance. Para 5 does the
        # same where the claimant's partner in a joint-claim couple is on
        # income-based JSA. The model cannot tell which of the claimant and
        # partner claims Housing Benefit (a couple choose, reg 82(1)), so it
        # applies the disregard whichever of them is on the benefit. Another
        # member's own award does not count: they claim in their own right
        # (in_receipt_of_income_support_jsa_ib_or_esa_ir). There is no age
        # condition: SI 2006/213 reg 5(1)(b) (NI: SR 2006/405 reg 5(1)(b))
        # applies these regulations to a claimant over the qualifying age for
        # State Pension Credit whose partner is on one of these benefits, so a
        # mixed-age couple whose younger member is on income-related ESA or
        # Universal Credit is covered. Universal Credit is read before the
        # benefit cap (housing_benefit_on_passporting_benefit), which avoids a
        # circular dependency through the cap.
        on_passporting_benefit = benunit(
            "housing_benefit_on_passporting_benefit", period
        )
        return where(passported | on_passporting_benefit, 0, applicable_income)
