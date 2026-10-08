from policyengine_uk.model_api import *


class incapacity_benefit_is_short_term_lower_rate(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "incapacity benefit is short term lower rate"
    documentation = "The person's reported Incapacity Benefit is the short-term lower rate. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
