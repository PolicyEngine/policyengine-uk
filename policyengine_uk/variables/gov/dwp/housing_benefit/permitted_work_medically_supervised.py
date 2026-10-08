from policyengine_uk.model_api import *


class permitted_work_medically_supervised(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "permitted work medically supervised"
    documentation = "The exempt work is part of prescribed medically supervised treatment as a hospital inpatient or regular outpatient. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
