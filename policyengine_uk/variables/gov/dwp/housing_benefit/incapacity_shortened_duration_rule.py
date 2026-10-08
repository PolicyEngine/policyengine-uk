from policyengine_uk.model_api import *


class incapacity_shortened_duration_rule(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "incapacity shortened duration rule"
    documentation = "The claimant meets the statutory serious-illness definition for the 196-day rather than 364-day old incapacity disregard route. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
