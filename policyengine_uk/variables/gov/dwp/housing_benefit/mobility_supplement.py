from policyengine_uk.model_api import *


class mobility_supplement(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "mobility supplement"
    documentation = "Reported war-disablement/personal-injury mobility supplement under the provisions listed in pension-age HB Schedule 4 paragraph 5. Defaults to zero/false when the factual history is not supplied."
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
