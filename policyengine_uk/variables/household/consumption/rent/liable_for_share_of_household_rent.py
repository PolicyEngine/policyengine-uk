from policyengine_uk.model_api import *


class liable_for_share_of_household_rent(Variable):
    value_type = bool
    entity = BenUnit
    label = "Liable for a share of the household's rent"
    documentation = (
        "Whether this family shares liability for the household's rent with "
        "the household head's family: a joint tenant, or a sharer with its "
        "own agreement for part of the same accommodation (the Family "
        "Resources Survey's shared household). The household head's family "
        "is always liable, so this matters only for other families. Boarders "
        "and lodgers, who pay the householder, are not sharers: see "
        "rent_paid_as_boarder and rent_paid_as_lodger."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/24",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/12B",
    )
