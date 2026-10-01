from policyengine_uk.model_api import *


class lha_renter_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "LHA renter has a non-dependant"
    documentation = (
        "Someone in this benefit unit who is neither a claimant or partner "
        "nor a child or young person, or, for the household head's family, a "
        "claimant or partner of another family who is a non-dependant of the "
        "household head (see is_non_dependant_of_household_head): joint "
        "tenants and other sharers of the rent, boarders and lodgers are not "
        "non-dependants, and a sharer, boarder or lodger has none from the "
        "household head's family. Foster children are not identified."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        # A child or young person under either scheme (UC reg 5; HB reg 19)
        # is a dependant, not a non-dependant.
        age = person("age", period)
        child_or_qyp = (
            person("is_child_or_qualifying_young_person_for_universal_credit", period)
            | person("is_child_or_young_person_for_legacy_benefits", period)
            | ((age >= 16) & (age < 17))
        )
        within_benefit_unit = benunit.any(~claimant_or_partner & ~child_or_qyp)
        # UC Regs 2013 Sch 4 para 9(2)(d)-(f); HB Regs 2006 reg 3(2)(d)-(e).
        non_dependant_claimants = claimant_or_partner & person(
            "is_non_dependant_of_household_head", period
        )
        head_family = benunit.any(person("is_household_head", period))
        other_family_non_dependants = head_family * benunit.max(
            person.household.sum(non_dependant_claimants)
        )
        return within_benefit_unit | (other_family_non_dependants > 0)
