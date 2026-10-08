from policyengine_uk.model_api import *


class housing_benefit_specified_occupation_net_earnings(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "housing benefit specified occupation net earnings"
    documentation = "Net earnings from the part-time firefighting, auxiliary coast rescue, part-time lifeboat and prescribed reserve-force employments listed in the applicable HB schedule; not other earnings. Defaults to zero/false when the factual history is not supplied."
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
