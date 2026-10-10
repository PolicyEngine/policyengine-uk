from policyengine_uk.model_api import *


class is_child_or_qualifying_young_person_for_pension_credit(Variable):
    """A child or qualifying young person the benefit unit is responsible for
    under Pension Credit Schedule IIA.

    A claimant is responsible for a child or qualifying young person who
    normally lives with them, which a claimant cannot be to themselves, but
    not for a qualifying young person they live with as a couple (State
    Pension Credit Regulations 2002 Sch. IIA para. 3(1)-(2)). So the benefit
    unit's claimant and partner are never its children or qualifying young
    persons, whatever their age or education. Nor is a child or qualifying
    young person looked after by a local authority (para. 4).
    """

    value_type = bool
    entity = Person
    label = "Child or qualifying young person for Pension Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IIA"

    def formula(person, period, parameters):
        child_or_qualifying_young_person = person(
            "is_child_for_pension_credit", period
        ) | person("is_qualifying_young_person_for_pension_credit", period)
        return (
            child_or_qualifying_young_person
            & ~person("is_claimant_or_partner", period)
            & ~person("is_looked_after_by_local_authority", period)
        )
