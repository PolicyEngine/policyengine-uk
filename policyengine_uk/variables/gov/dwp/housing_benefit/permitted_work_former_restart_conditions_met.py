from policyengine_uk.model_api import *


class permitted_work_former_restart_conditions_met(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "permitted work former restart conditions met"
    documentation = "The pre-April-2017 statutory conditions allowing this higher-limit work period to start/restart have been satisfied. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
