from policyengine_uk.model_api import *


class housing_benefit_ni_additional_occupation_net_earnings(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "housing benefit ni additional occupation net earnings"
    documentation = "Net earnings from additional Northern Ireland prescribed part-time army/PSNI reserve or trainee employments, included only for a Northern Ireland claim. Defaults to zero/false when the factual history is not supplied."
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
