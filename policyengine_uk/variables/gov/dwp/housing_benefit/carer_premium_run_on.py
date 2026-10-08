from policyengine_uk.model_api import *


class carer_premium_run_on(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "carer premium run on"
    documentation = "A carer premium continues in respect of this person under its statutory run-on rule after their carer-benefit entitlement ended. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
