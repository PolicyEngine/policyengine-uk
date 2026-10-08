from policyengine_uk.model_api import *


class permitted_work_weeks(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "permitted work weeks"
    documentation = "Weeks in the current ordinary higher-limit permitted-work period under the former 52-week restriction. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
