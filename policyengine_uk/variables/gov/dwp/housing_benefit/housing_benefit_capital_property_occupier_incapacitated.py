from policyengine_uk.model_api import *


class housing_benefit_capital_property_occupier_incapacitated(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital property occupier incapacitated"
    documentation = "That occupier is incapacitated under the applicable capital rule. False unless supplied; refers to the occupier of this capital owner's property, who may live outside the modelled household."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
    )
