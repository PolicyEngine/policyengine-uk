from policyengine_uk.model_api import *


class permitted_work_net_earnings(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "permitted work net earnings"
    documentation = "Weekly earnings from the particular work assessed as exempt, calculated under the relevant ESA/incapacity rules. Other jobs are excluded from this input. Defaults to zero/false when the factual history is not supplied."
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
