from policyengine_uk.model_api import *


class has_non_resident_overnight_carer(Variable):
    value_type = bool
    entity = Person
    label = "has a non-resident overnight carer"
    documentation = (
        "Whether one or more people who do not live in the home are engaged, "
        "under arrangements made for that purpose, to provide this person "
        "with overnight care and to stay overnight in the home on a regular "
        "basis. With a qualifying disability benefit, this can give an "
        "additional bedroom in the Universal Credit and Housing Benefit size "
        "criteria (see meets_lha_overnight_care_condition): to the renter "
        "whose extended benefit unit the person is in, or who fosters them "
        "(UC), or to the claimant whose dwelling they occupy (HB). A "
        "lodger's or joint tenant's carer gives the household head's family "
        "nothing under Universal Credit."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
    )
