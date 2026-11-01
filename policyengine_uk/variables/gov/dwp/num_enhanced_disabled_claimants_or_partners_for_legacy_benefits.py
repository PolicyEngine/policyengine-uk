from policyengine_uk.model_api import *


class num_enhanced_disabled_claimants_or_partners_for_legacy_benefits(Variable):
    value_type = int
    entity = BenUnit
    label = "Enhanced-disabled claimants or partners for legacy benefits"
    documentation = (
        "The model counts the claimants and partners who meet the enhanced "
        "disability premium condition: they receive a qualifying benefit "
        "(receives_enhanced_disability_premium_qualifying_benefit) and have "
        "not attained the qualifying age for State Pension Credit. Under the "
        "Housing Benefit and Jobseeker's Allowance Regulations, the Welsh "
        "Council Tax Reduction scheme and England's Default Scheme, the age "
        "limit applies to the claimant and to family members or partners. "
        "Parliament limits Income Support and Employment and Support "
        "Allowance to claimants under that age (SSCBA 1992 s.124(1)(aa) and "
        "SSCBA (NI) 1992 s.123(1)(aa); WRA 2007 s.1(3)(c) and WRA (NI) 2007 "
        "s.1(3)(c), pensionable age), so their Regulations state the age "
        "limit only for the partner. The count leaves out children and young "
        "persons, whose separate enhanced premium the model computes for "
        "Housing Benefit only (housing_benefit_child_disability_premiums)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/15",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13A",
        "https://www.legislation.gov.uk/uksi/2008/794/schedule/4/paragraph/7",
        "https://www.legislation.gov.uk/uksi/1996/207/schedule/1/paragraph/15A",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4/paragraph/15",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/12",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        qualifying = person(
            "receives_enhanced_disability_premium_qualifying_benefit", period
        )
        # "who has not attained the qualifying age for state pension credit"
        # (HB Regs 2006 Sch 3 para 15(1)(b)-(d); IS Regs 1987 Sch 2 para
        # 13A(1)(b)).
        under_age = ~person("has_attained_state_pension_credit_qualifying_age", period)
        return benunit.sum(claimant_or_partner & qualifying & under_age)
