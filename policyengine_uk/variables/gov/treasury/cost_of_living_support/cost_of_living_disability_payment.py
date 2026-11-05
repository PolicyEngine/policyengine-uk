from policyengine_uk.model_api import *


class cost_of_living_disability_payment(Variable):
    label = "Disability cost-of-living payment"
    documentation = (
        "The Disability Cost of Living Payment to the person in the year. The "
        "Secretary of State pays it to each individual with a qualifying "
        "disability benefit, so each person in a household who has one gets "
        "it."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/2022/38/section/5",
        "https://www.legislation.gov.uk/ukpga/2023/7/section/5",
    ]

    def formula(person, period, parameters):
        p = parameters(period).gov.treasury.cost_of_living_support.disabled
        on_benefit = add(person, period, p.qualifying_benefits) > 0
        return p.amount * on_benefit
