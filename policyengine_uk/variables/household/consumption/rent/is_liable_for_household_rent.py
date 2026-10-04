from policyengine_uk.model_api import *


class is_liable_for_household_rent(Variable):
    value_type = bool
    entity = Person
    label = "Liable for the household's rent"
    documentation = (
        "Whether this person is one of the people liable for the rent of the "
        "household's accommodation: the claimant or partner of the household "
        "head's family, or of a family liable for a share of that rent."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/24",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/12B",
    )

    def formula(person, period, parameters):
        head_family = person.benunit.any(person("is_household_head", period))
        sharer = person.benunit("liable_for_share_of_household_rent", period)
        return person("is_claimant_or_partner", period) & (head_family | sharer)
