from policyengine_uk.model_api import *


class ebr_energy_bills_credit_eligible(Variable):
    label = "Eligible for the Energy Bills Support Scheme credit"
    documentation = (
        "Whether the household has a qualifying domestic electricity supply for "
        "the main Energy Bills Support Scheme. The model defaults to true because "
        "it does not otherwise represent electricity contracts or meter points."
    )
    entity = Household
    definition_period = MONTH
    value_type = bool
    default_value = True
    reference = (
        "https://assets.publishing.service.gov.uk/media/661eb96a90095817cebd3dc7/withdrawn-ebss-guidance-for-electricity-suppliers.pdf#page=16",
        "https://assets.publishing.service.gov.uk/media/63a59ed48fa8f5654fe0a812/ebss-ni-direction.pdf#page=2",
    )
