from policyengine_uk.model_api import *


class permitted_work_supported(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "permitted work supported"
    documentation = "The exempt work is supervised by the prescribed public/local authority or qualifying voluntary/community-interest organisation worker. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
