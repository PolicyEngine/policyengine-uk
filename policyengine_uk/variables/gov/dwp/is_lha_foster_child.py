from policyengine_uk.model_api import *


class is_lha_foster_child(Variable):
    value_type = bool
    entity = Person
    label = "Foster child in the Universal Credit size criteria"
    documentation = (
        "A person under 18 looked after by a local authority and placed with "
        "the claimant or partner of their benefit unit. The renter is their "
        "foster parent (UC Regs 2013 reg 2, a person with whom a child is "
        "placed under the care planning regulations, where a child is a "
        'person under 18). The model reads "foster child" in Sch 4 para '
        '9(3) and "a child" in para 12(A1)(c) the same way, so a foster '
        "child aged 16 or 17 is not a non-dependant and has no bedroom of "
        "their own, and their overnight care counts for the renter. The "
        "narrower reading, under 16 as in the Welfare Reform Act 2012 s.40, "
        "would instead make such a person a non-dependant with a bedroom "
        "and give the renter no foster room. The guidance does not settle "
        "which applies."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/ukpga/1989/41/section/105",
    )

    def formula(person, period, parameters):
        age_limit = parameters(period).gov.dwp.LHA.foster_child_age_limit
        return (
            person("is_looked_after_by_local_authority", period)
            & (person("age", period) < age_limit)
            & ~person("is_claimant_or_partner", period)
        )
