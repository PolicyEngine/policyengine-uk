from policyengine_uk.model_api import *


class is_qualifying_young_person_for_universal_credit(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person for Universal Credit"
    documentation = (
        "A qualifying young person under UC Regs 2013 reg. 5 "
        "(is_qualifying_young_person_under_universal_credit_regulation_5): a "
        "person aged 16 to 19 who meets reg. 5(1)(a) or (b) and receives no "
        "Universal Credit, contributory ESA or contribution-based JSA (reg. "
        "5(5)) and no existing benefit: income-based JSA, income-related ESA, "
        "Income Support, Housing Benefit, Child Tax Credit or Working Tax "
        "Credit (SI 2014/1230 regs. 2(1) and 28; SR 2016/226 regs. 2(1) and "
        "29). The Secretary of State ties the exclusion to entitlement (reg. "
        "28), so the formula reads a report only in a year the model pays that "
        "benefit, only until the model's legacy closure, or for a claimant or "
        "partner the family's Universal Credit claim, ends the award on it, and"
        " only if no reform neutralises it. It doesn't apply the model's other "
        "conditions of payment, so a report can exclude a person even where the"
        " model pays nothing on that report. For example, the model pays Income"
        " Support only on the claimant's and partner's reports, Housing Benefit"
        " only to a family that rents, and income-based JSA and income-related "
        "ESA only after their capital and work screens. The model pays Income "
        "Support, income-based JSA and tax credits only while "
        "gov.dwp.income_support.active, gov.dwp.JSA.income.active and "
        "gov.dwp.tax_credits.active hold, has no closure date for Housing "
        "Benefit, and pays an income-related ESA claim only while it stays "
        "payable (esa_income_payable_share), so the formula reads its report "
        "only then. The formula also reads the Income Support, income-based "
        "JSA and tax credit reports while "
        "gov.contrib.policyengine.disable_simulated_benefits is on. The reform "
        "that switch turns on pays them at their reported amounts in the "
        "dataset year and the nine years after it, and the formula still reads "
        "them in later years. In those years the reform also pays a claimant's "
        "or partner's own income-related ESA, Housing Benefit and Child Tax "
        "Credit report whether or not the family claims Universal Credit, so "
        "while the switch is on the formula leaves out the Universal Credit "
        "claim limbs below. It leaves them out in later years too, when the "
        "model again ends those awards on the family's claim. The model also ends"
        " a person's legacy awards once its annual migration proxy closes them:"
        " it ends their Income Support, income-based JSA and income-related ESA"
        " when person_legacy_benefits_closed holds, the family's tax credits "
        "when legacy_benefits_closed holds, and its Housing Benefit when "
        "legacy_benefits_closed holds and the family doesn't meet the Pension "
        "Credit age conditions. The formula follows both closures. A claim for "
        "Universal Credit ends the claimant's and partner's own awards (SI "
        "2014/1230 reg. 8(2) and (2A); SI 2013/983 art. 4), and the model ends "
        "the family's continuing Housing Benefit award "
        "(housing_benefit_eligible) and its Child Tax Credit (is_CTC_eligible),"
        " and the claimant's and partner's income-related ESA "
        "(esa_income_report_closed), when the family claims "
        "(claims_universal_credit). For a claimant or partner, the formula "
        "follows those limbs too. The family's claim doesn't end a dependant's "
        "own award, so for a dependant the formula doesn't. The model ends no "
        "Working Tax Credit, Income Support or income-based JSA award on the "
        "claim, so the formula follows no claim limb for them. It can't read "
        "housing_benefit_eligible: that variable's Pension Credit route reads "
        "left_pension_route_at_legacy_closure, which reads this variable "
        "through is_uc_entitled and the child element. So the formula keeps a "
        "Housing Benefit report while the family meets the Pension Credit age "
        "conditions. The formula checks each report against its own variable: "
        "income_support, jsa_income, esa_income, housing_benefit, "
        "child_tax_credit or tax_credits for Child Tax Credit, and "
        "working_tax_credit or tax_credits for Working Tax Credit. A reform "
        "that changes or zeroes a benefit's formula without neutralising its "
        "variable leaves the exclusion on that benefit's reports in place. For "
        "a claimant or partner it also reads the couple's joint tax credit "
        "award (Tax Credits Act 2002 s.3(3)), each credit by its own check."
    )
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/2",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2013/983/article/4",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/29",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/2",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
    ]

    def formula(person, period, parameters):
        return qualifying_young_person(person, period, parameters)


def qualifying_young_person(person, period, parameters, at_claim_start=False):
    """The UC qualifying young person test with SI 2014/1230 reg. 28
    applied, as is_qualifying_young_person_for_universal_credit documents
    it. With at_claim_start it gives a claimant's or partner's status on the
    first day of their Universal Credit award
    (is_qualifying_young_person_for_uc_education reads it). A Housing
    Benefit or income-related ESA award the claim ends still runs that day
    (reg. 8(2A); esa_income_report_closed's run-on), so the formula leaves
    out those two claim limbs. The claim has already ended a tax credit
    award (reg. 8(2)(a)), so the formula keeps the Child Tax Credit limb.
    The year gates and the legacy closures apply either way."""
    # The Secretary of State excludes a person entitled to an existing
    # benefit (TP regs. 2(1) and 28). The formula reads raw person-level
    # reports, the model's legacy closure proxy and the family's Universal
    # Credit claim, so it calculates no family benefit that depends on QYP
    # status.
    p = parameters(period).gov
    dwp = p.dwp
    # The reform pays each listed benefit at its dataset-year report in
    # that year and the nine after it, closure dates included, and holds
    # both legacy closures false in those years. The formula reads the
    # switch, not those years, so in a later year it still reads a tax
    # credit report that the model no longer pays, and still leaves out
    # the claim limbs below.
    paid_as_reported = bool(p.contrib.policyengine.disable_simulated_benefits)
    system = person.simulation.tax_benefit_system

    def paying(active, *names):
        # Nobody is entitled to a benefit the model no longer pays, or one
        # a reform neutralises.
        return bool(active or paid_as_reported) and not any(
            system.get_variable(name).is_neutralized for name in names
        )

    # The model ends a person's Income Support, income-based JSA and
    # income-related ESA when their legacy awards close: the claimant's
    # and partner's together (legacy_benefits_closed, read through
    # income_support), and anyone else's on their own reports
    # (jsa_income, esa_income). person_legacy_benefits_closed and
    # legacy_benefits_closed read reports, is_claimant_or_partner, the
    # Pension Credit age conditions and parameters, and no Universal
    # Credit variable.
    own_award_open = ~person("person_legacy_benefits_closed", period)
    # A claim for Universal Credit ends the claimant's and partner's own
    # awards (SI 2014/1230 reg. 8(2) and (2A); SI 2013/983 art. 4), and
    # nobody else's. The model ends the claimant's and partner's
    # income-related ESA when the family claims (esa_income_report_closed),
    # and the formula follows it. claims_universal_credit reads
    # would_claim_uc, would_claim_uc_at_legacy_closure and
    # legacy_benefits_closed, not this variable. In its years the reform
    # behind disable_simulated_benefits pays each report as reported
    # whether or not the family claims, and holds the legacy closures
    # false, so while the switch is on the formula keeps the person's own
    # closure alone.
    claimant_or_partner = person("is_claimant_or_partner", period)
    # The Secretary of State (SI 2025/1148 art. 3A) and, in Northern
    # Ireland, the Department for Communities (SR 2025/176 art. 3A) end old
    # style income-related ESA claims on the appointed date unless an
    # appointee saving keeps them (esa_income_payable_share).
    esa_income_open = (
        ~person("esa_income_report_closed", period)
        | (own_award_open & (paid_as_reported or at_claim_start))
    ) & ((person("esa_income_payable_share", period) > 0) | paid_as_reported)
    claim_ends_own_award = (
        claimant_or_partner
        & person.benunit("claims_universal_credit", period)
        & (not paid_as_reported)
    )
    # On the first day of the award a Housing Benefit award the claim ends
    # still runs (reg. 8(2A)).
    claim_has_ended_housing_benefit = claim_ends_own_award & (not at_claim_start)
    # The model pays Housing Benefit and tax credits to the family, on
    # every member's reports, and ends them when the claimant's and
    # partner's legacy awards close (housing_benefit_eligible,
    # is_CTC_eligible, is_WTC_eligible). It also ends the family's
    # continuing Housing Benefit award and its Child Tax Credit when the
    # family claims Universal Credit, and the formula follows that limb
    # for a claimant or partner, whose own award the claim ends. A family
    # that meets the Pension Credit age conditions keeps Housing Benefit
    # unless it claims Universal Credit at the closure and is entitled to
    # it (left_pension_route_at_legacy_closure). That variable reads this
    # one through is_uc_entitled and the child element, so the formula
    # keeps the Housing Benefit report for such a family.
    family_closed = person.benunit("legacy_benefits_closed", period)
    family_award_open = ~family_closed
    housing_benefit_open = person.benunit(
        "meets_pension_credit_age_conditions", period
    ) | (~family_closed & ~claim_has_ended_housing_benefit)

    income_support_paying = (
        paying(dwp.income_support.active, "income_support") & own_award_open
    )
    jsa_income_paying = paying(dwp.JSA.income.active, "jsa_income") & own_award_open
    esa_income_paying = paying(True, "esa_income") & esa_income_open
    housing_benefit_paying = paying(True, "housing_benefit") & housing_benefit_open
    child_tax_credit_paying = (
        paying(dwp.tax_credits.active, "child_tax_credit", "tax_credits")
        & family_award_open
        & ~claim_ends_own_award
    )
    working_tax_credit_paying = (
        paying(dwp.tax_credits.active, "working_tax_credit", "tax_credits")
        & family_award_open
    )
    tax_credits_reported = child_tax_credit_paying * person(
        "child_tax_credit_reported", period
    ) + working_tax_credit_paying * person("working_tax_credit_reported", period)
    # Tax Credits Act 2002 s.3(3): the members of a couple claim jointly,
    # so the couple's award belongs to the claimant and the partner. A
    # dependant claims as a single person, so their award stays theirs.
    couple_tax_credits_reported = person.benunit.sum(
        where(claimant_or_partner, tax_credits_reported, 0)
    )
    receives_tax_credits = (tax_credits_reported > 0) | (
        claimant_or_partner & (couple_tax_credits_reported > 0)
    )
    entitled_to_existing_benefit = (
        (esa_income_paying & (person("esa_income_reported", period) > 0))
        | (jsa_income_paying & (person("jsa_income_reported", period) > 0))
        | (income_support_paying & (person("income_support_reported", period) > 0))
        | (housing_benefit_paying & (person("housing_benefit_reported", period) > 0))
        | receives_tax_credits
    )
    return (
        person(
            "is_qualifying_young_person_under_universal_credit_regulation_5",
            period,
        )
        & ~entitled_to_existing_benefit
    )
