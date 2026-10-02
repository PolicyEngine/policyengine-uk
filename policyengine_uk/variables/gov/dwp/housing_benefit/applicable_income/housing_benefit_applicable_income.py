from policyengine_uk.model_api import *


class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "relevant income for Housing Benefit means test"
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
        any_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
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
            # Counted by both regimes: HB (SPC) Regs 2006 reg 29(1)(j), which
            # excepts only the IIDB increases under SSCBA ss.104-105 and Sch 8
            # (heads (iii)-(v)), and HB Regs 2006 reg 40 with Sch 5, whose
            # para 9 attendance allowance disregard covers the ss.104-105
            # increases (reg 2(1)). iidb is the whole reported payment and
            # cannot separate those increases.
            "iidb",
            "sda",
            "incapacity_benefit",
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
        applicable_income = max_(
            0,
            increased_income_reduced_by_tax_and_pensions
            + tariff_income
            - disregard
            - childcare_element,
        )
        guarantee_credit = any_over_SP_age & (benunit("guarantee_credit", period) > 0)
        return where(guarantee_credit, 0, applicable_income)
