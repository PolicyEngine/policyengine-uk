from policyengine_uk.model_api import *


class housing_benefit_special_disregard_max_award_break_weeks(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "housing benefit special disregard max award break weeks"
    documentation = "Longest break in HB entitlement since the qualifying protected award, in weeks. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
