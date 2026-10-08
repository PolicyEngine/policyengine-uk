from policyengine_uk.model_api import *


class housing_benefit_capital_premises_intended_home(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital premises intended home"
    documentation = "The claimant intends to occupy the supplied acquired/possession/repair premises as their home. False unless supplied; refers to the occupier of this capital owner's property, who may live outside the modelled household."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
    )
