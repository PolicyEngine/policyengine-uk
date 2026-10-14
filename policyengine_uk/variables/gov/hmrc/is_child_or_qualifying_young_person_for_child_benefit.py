from policyengine_uk.model_api import *


class is_child_or_qualifying_young_person_for_child_benefit(Variable):
    """A child or qualifying young person whom the benefit unit can claim
    Child Benefit for.

    Child Benefit goes to a person responsible for a child or qualifying
    young person (SSCBA 1992 s.141): someone who has them living with them or
    contributes to their keep (s.143(1)). A person is not responsible for
    themselves, and no one gets Child Benefit for a qualifying young person
    who is their spouse, civil partner or partner (Child Benefit (General)
    Regulations 2006 regs 12 and 13). So the benefit unit's claimant and
    partner are never its children or qualifying young persons, whatever
    their age or education. Someone responsible for them in another benefit
    unit is not modelled.
    """

    value_type = bool
    entity = Person
    label = "Child or qualifying young person for Child Benefit"
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/ukpga/1992/4/section/141",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/142",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/143",
        "https://www.legislation.gov.uk/uksi/2006/223",
        "https://www.legislation.gov.uk/uksi/2006/223/regulation/12",
        "https://www.legislation.gov.uk/uksi/2006/223/regulation/13",
    ]

    def formula(person, period, parameters):
        child_or_qualifying_young_person = person(
            "is_child_for_child_benefit", period
        ) | person("is_qualifying_young_person_for_child_benefit", period)
        return child_or_qualifying_young_person & ~person(
            "is_claimant_or_partner", period
        )
