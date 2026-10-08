from policyengine_uk.model_api import *


class working_tax_credit_disability_element_in_award(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "working tax credit disability element in award"
    documentation = "A disability/severe-disability element is included in the person's actual Working Tax Credit award. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
