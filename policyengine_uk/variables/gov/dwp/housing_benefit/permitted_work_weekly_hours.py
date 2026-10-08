from policyengine_uk.model_api import *


class permitted_work_weekly_hours(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "permitted work weekly hours"
    documentation = "Average weekly hours in the work assessed as exempt, excluding separate other work. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
