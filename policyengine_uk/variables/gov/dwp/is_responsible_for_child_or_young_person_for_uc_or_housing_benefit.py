from policyengine_uk.model_api import *


class is_responsible_for_child_or_young_person_for_uc_or_housing_benefit(Variable):
    """Responsible for a child or young person under UC or Housing Benefit rules.

    A union of the two schemes' tests that no formula reads; the reference
    formulas in test_benefit_cap_lha_scheme_split_properties.py read it as
    the rule before the schemes were split. UC counts a
    child or qualifying young person (UC Regs 2013 regs 4-5); Housing Benefit
    counts a child or young person, whose young-person test follows Child
    Benefit (HB Regs 2006 regs 2, 19). Each scheme's rules read its own test:
    Universal Credit's LHA shared accommodation test
    (is_lha_shared_accommodation_rate_specified_renter) reads
    is_responsible_for_child_or_qualifying_young_person_for_universal_credit
    (UC Sch 4 para 28(3)), and counts a Housing Benefit young person who is
    not a UC qualifying young person as a non-dependant
    (universal_credit_renter_has_non_dependant; para 28(4)). Housing
    Benefit's test, housing_benefit_LHA_category, reads
    is_housing_benefit_young_individual and housing_benefit_has_non_dependant
    (HB reg 13D(2)(a)(i)). The benefit cap rates read each scheme's own
    responsibility test.

    The union also counts every 16-year-old in the benefit unit who is not a
    claimant or partner, for the year.
    """

    value_type = bool
    entity = BenUnit
    label = "Responsible for a child or young person (UC or Housing Benefit)"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/19",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        age = person("age", period)
        sixteen = (age >= 16) & (age < 17) & ~person("is_claimant_or_partner", period)
        return (
            benunit(
                "is_responsible_for_child_or_qualifying_young_person_for_universal_credit",
                period,
            )
            | benunit(
                "is_responsible_for_child_or_young_person_for_legacy_benefits", period
            )
            | benunit.any(sixteen)
        )
