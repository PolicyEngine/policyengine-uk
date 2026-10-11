from policyengine_uk.model_api import *


class is_child_or_qualifying_young_person_for_child_tax_credit(Variable):
    """A child or qualifying young person the benefit unit is responsible for
    under the Child Tax Credit rules.

    A claimant is responsible for a child or qualifying young person who
    normally lives with them (Child Tax Credit Regulations 2002 reg. 3(1)
    Rule 1), which a claimant cannot be to themselves. No one is responsible
    for a qualifying young person who is the responsible person's partner, or
    who lives with a partner not in full-time education or approved training
    (Cases G and H). Nor for one who claims and is awarded child tax credit
    in their own right for a child they are responsible for (Case D), or who
    claims and receives working tax credit in their own right (Case F). So
    the benefit unit's claimant and partner (Tax Credits Act 2002 s.3) are
    never its children or qualifying young persons. Nor is a child or
    qualifying young person looked after by a local authority (Case A).
    """

    value_type = bool
    entity = Person
    label = "Child or qualifying young person for Child Tax Credit"
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/8",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/3",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/5",
    ]

    def formula(person, period, parameters):
        child_or_qualifying_young_person = person(
            "is_child_for_child_tax_credit", period
        ) | person("is_qualifying_young_person_for_child_tax_credit", period)
        return (
            child_or_qualifying_young_person
            & ~person("is_claimant_or_partner", period)
            & ~person("is_looked_after_by_local_authority", period)
        )
