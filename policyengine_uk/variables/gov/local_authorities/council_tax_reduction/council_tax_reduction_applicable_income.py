from policyengine_uk.model_api import *


class council_tax_reduction_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "relevant income for Council Tax Reduction means test"
    documentation = (
        "The income of the Council Tax Reduction applicant and partner "
        "(is_council_tax_reduction_applicant_or_partner), with, as the model "
        "did before, the income of the family's children or young persons. "
        "The benefit unit's own benefits (Child Benefit, Income Support, "
        "income-based Jobseeker's Allowance, income-related Employment and "
        "Support Allowance, Universal Credit and tax credits) count only where "
        "the applicant is the benefit unit's claimant: where the household "
        "head applies alone, those awards and children belong to the benefit "
        "unit's claimant and partner, not to the head."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/21",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/11",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/5",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/7",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/36",
    )

    def formula(benunit, period, parameters):
        # Members whose income counts: the applicant and partner and, as the model
        # did before, the programme's own children or young persons. The regulations
        # count only the applicant's and partner's (CTR (Prescribed Requirements)
        # (England) Regs 2012 Sch 1 para 11; SSI 2012/319 reg 21(3) and SSI
        # 2021/249 reg 36(2) exclude a child's); dropping dependants' own income is
        # a follow-up. Anyone else in the benefit unit does not count.
        person = benunit.members
        head_applies_alone = benunit("council_tax_reduction_head_applies_alone", period)
        applicant_family = ~head_applies_alone
        members = person("is_council_tax_reduction_applicant_or_partner", period) | (
            person("is_child_or_young_person_for_legacy_benefits", period)
            & benunit.project(applicant_family)
        )
        benunit_means_tested_benefits = [
            "child_benefit",
            "income_support",
            "jsa_income",
            "esa_income",
            "universal_credit",
        ]
        personal_benefits = [
            "carers_allowance",
            "esa_contrib",
            "jsa_contrib",
            "state_pension",
            "maternity_allowance",
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "ssmg",
        ]
        income_components = [
            "employment_income",
            "self_employment_income",
            "property_income",
            "private_pension_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        # The benefit unit's awards are its claimant's and partner's.
        benefits = applicant_family * add(
            benunit, period, benunit_means_tested_benefits
        )
        income = add_for_members(benunit, period, income_components, members)
        personal_benefit_income = add_for_members(
            benunit, period, personal_benefits, members
        )
        credits = applicant_family * add(benunit, period, ["tax_credits"])
        increased_income = income + personal_benefit_income + credits + benefits

        if not bi.interactions.include_in_means_tests:
            increased_income -= add_for_members(
                benunit, period, ["basic_income"], members
            )

        pension_contributions = (
            add_for_members(benunit, period, ["pension_contributions"], members) * 0.5
        )
        tax = add_for_members(
            benunit, period, ["income_tax", "national_insurance"], members
        )
        return max_(0, increased_income - tax - pension_contributions)
