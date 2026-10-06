from policyengine_uk.model_api import *


class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "relevant income for Housing Benefit means test"
    documentation = (
        "Income taken into account in the Housing Benefit means test. It is "
        "nil for a family on Universal Credit, Income Support, income-based "
        "Jobseeker's Allowance or income-related Employment and Support "
        "Allowance (housing_benefit_on_passporting_benefit), whose whole "
        "income is disregarded, and for a pension-age family with a positive "
        "guarantee credit (the guarantee credit passport). Where the Pension "
        "Credit award is savings credit only, it is the Secretary of State's "
        "assessment of income plus the savings credit payable, less childcare "
        "charges and the earnings disregards. Otherwise it is the family's "
        "income under the Housing Benefit rules."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/4",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/6/paragraph/4",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/5",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/26",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/24",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/25",
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant and partner and, as the model did
        # before, the programme's own children or young persons. The regulations count
        # only the claimant's and partner's (HB Regs 2006 reg 25); dropping dependants'
        # own income is a follow-up. Anyone else in the benefit unit does not count.
        person = benunit.members
        members = person("is_claimant_or_partner", period) | person(
            "is_child_or_young_person_for_legacy_benefits", period
        )
        pension_age_regulations = benunit(
            "housing_benefit_pension_age_regulations_apply", period
        )
        BENUNIT_MEANS_TESTED_BENEFITS = [
            "child_benefit",
            "income_support",
            "jsa_income",
            "esa_income",
        ]
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
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "ssmg",
        ]
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "property_income",
            "private_pension_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        # Add personal benefits, credits and total benefits to income
        benefits = add_for_members(
            benunit, period, BENUNIT_MEANS_TESTED_BENEFITS, members
        )
        income = add_for_members(benunit, period, INCOME_COMPONENTS, members)
        personal_benefits = add_for_members(benunit, period, PERSONAL_BENEFITS, members)
        credits = add_for_members(benunit, period, ["tax_credits"], members)
        increased_income = income + personal_benefits + credits + benefits

        if not bi.interactions.include_in_means_tests:
            # Basic income is already in personal benefits, deduct if needed
            increased_income -= add_for_members(
                benunit, period, ["basic_income"], members
            )
        # Reduce increased income by pension contributions and tax
        pension_contributions = (
            add_for_members(benunit, period, ["pension_contributions"], members) * 0.5
        )
        TAX_COMPONENTS = ["income_tax", "national_insurance"]
        tax = add_for_members(benunit, period, TAX_COMPONENTS, members)
        increased_income_reduced_by_tax_and_pensions = (
            increased_income - tax - pension_contributions
        )
        tariff_income = benunit("housing_benefit_tariff_income", period)
        disregard = benunit("housing_benefit_applicable_income_disregard", period)
        childcare_element = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        income_under_general_rules = max_(
            0,
            increased_income_reduced_by_tax_and_pensions
            + tariff_income
            - disregard
            - childcare_element,
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
        # Pension HB reg 26 disregards "the whole of his capital and income"
        # for guarantee-credit recipients within that regulation set.
        guarantee_credit = pension_age_regulations & (
            benunit("guarantee_credit", period) > 0
        )
        # SI 2006/213 Sch 5 para 4 (NI: SR 2006/405 Sch 6 para 4) disregards
        # "the whole of his income" where a claimant is on universal credit,
        # income support, an income-based jobseeker's allowance or an
        # income-related employment and support allowance. Para 5 does the
        # same where the claimant's partner in a joint-claim couple is on
        # income-based JSA. The model holds these awards for the benefit unit
        # and cannot tell which member claims Housing Benefit (a couple
        # choose, reg 82(1)), so it applies the disregard whichever member is
        # on the benefit. There is no age condition: SI 2006/213 reg 5(1)(b)
        # (NI: SR 2006/405 reg 5(1)(b)) applies these regulations to a
        # claimant over the qualifying age for State Pension Credit whose
        # partner is on one of these benefits, so a mixed-age couple whose
        # younger member is on income-related ESA or Universal Credit is
        # covered. Universal Credit is read before the benefit cap
        # (housing_benefit_on_passporting_benefit), which avoids a circular
        # dependency through the cap.
        on_passporting_benefit = benunit(
            "housing_benefit_on_passporting_benefit", period
        )
        return where(guarantee_credit | on_passporting_benefit, 0, applicable_income)
