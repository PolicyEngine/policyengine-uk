from policyengine_uk.model_api import *


class is_benefit_unit_non_dependant_for_universal_credit(Variable):
    value_type = bool
    entity = Person
    label = "Non-dependant within the benefit unit for Universal Credit"
    documentation = (
        "A member of the benefit unit, aged 16 or over, who is neither the "
        "claimant or partner nor a qualifying young person. The benefit unit "
        "follows the survey's family, which can include an adult child or a "
        "16 to 19 year old who is not a qualifying young person. In Universal "
        "Credit law such a person is not in the claimant's family but is a "
        "non-dependant of the renter: they normally live in the accommodation "
        "and are none of the persons excluded by Sch 4 para 9(2). A qualifying "
        "young person the renter is responsible for is a member of the "
        "renter's extended benefit unit, and one no one is responsible for, "
        "for example one looked after by a local authority, is excluded by "
        "para 9(2)(g). A child, under 16, is always one or the other."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/40",
    )

    def formula(person, period, parameters):
        # UC Regs 2013 Sch 4 para 9(1)(a)-(b) and (2)(a), (g); WRA 2012 s.40.
        not_a_child = ~person("is_child_for_universal_credit", period)
        claimant_or_partner = person("is_claimant_or_partner", period)
        qualifying_young_person = person(
            "is_qualifying_young_person_for_universal_credit", period
        )
        return not_a_child & ~claimant_or_partner & ~qualifying_young_person
