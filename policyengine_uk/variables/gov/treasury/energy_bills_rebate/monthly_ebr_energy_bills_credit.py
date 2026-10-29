from policyengine_uk.model_api import *


class monthly_ebr_energy_bills_credit(Variable):
    label = "Monthly Energy Bills Support Scheme credit"
    documentation = (
        "Main-scheme entitlement for the month. Alternative-funding payments and "
        "Northern Ireland's separate Alternative Fuel Payment are not included."
    )
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = GBP
    defined_for = "ebr_energy_bills_credit_eligible"
    reference = (
        "https://assets.publishing.service.gov.uk/media/661eb96a90095817cebd3dc7/withdrawn-ebss-guidance-for-electricity-suppliers.pdf#page=16",
        "https://assets.publishing.service.gov.uk/media/63a59ed48fa8f5654fe0a812/ebss-ni-direction.pdf#page=2",
    )

    def formula(household, period, parameters):
        return ebss_credit(parameters, period, household("country", period.this_year))


def ebss_credit(parameters, month, country):
    """The main-scheme credit for ``month`` to a household in ``country``."""
    ebr = parameters(month).gov.treasury.energy_bills_rebate
    is_northern_ireland = country == country.possible_values.NORTHERN_IRELAND
    return where(
        is_northern_ireland,
        ebr.energy_bills_credit_northern_ireland,
        ebr.energy_bills_credit_monthly,
    )
