from policyengine_uk.model_api import *


class uc_is_adopter_in_first_year(Variable):
    value_type = bool
    entity = Person
    label = "Adopter within 12 months of the placement, for Universal Credit"
    documentation = (
        "Whether the claimant is an adopter and it is 12 months or less since "
        "the child was placed with them (or since a date they chose within "
        "the 14 days before the expected placement). An adopter is someone "
        "matched with a child for adoption who is, or is intended to be, the "
        "responsible carer, other than a foster parent or close relative of "
        "the child. Such a claimant is subject to no work-related "
        "requirements. An input: the model has no adoption data."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/89"
    definition_period = YEAR
    default_value = False
