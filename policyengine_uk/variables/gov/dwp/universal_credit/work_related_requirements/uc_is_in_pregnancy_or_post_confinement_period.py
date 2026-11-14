from policyengine_uk.model_api import *


class uc_is_in_pregnancy_or_post_confinement_period(Variable):
    value_type = bool
    entity = Person
    label = "Pregnant within 11 weeks of the expected week of confinement, or within 15 weeks after it, for Universal Credit"
    documentation = (
        'Whether the claimant "is pregnant and it is 11 weeks or less before '
        "her expected week of confinement, or was pregnant and it is 15 weeks "
        'or less since the date of her confinement". Such a claimant is '
        "subject to no work-related requirements. An input: the model has no "
        "pregnancy data."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/89"
    definition_period = YEAR
    default_value = False
