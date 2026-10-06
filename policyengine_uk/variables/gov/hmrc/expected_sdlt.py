from policyengine_uk.model_api import *


class expected_sdlt(Variable):
    label = "Stamp Duty (expected)"
    documentation = (
        "Expected annual Stamp Duty Land Tax on the household's own property "
        "purchases and leases. Population datasets mark only the households "
        "that buy property in the year as purchasers, so this is "
        "stamp_duty_land_tax with no further scaling. SDLT paid by "
        "corporations and incident on the household is corporate_sdlt, which "
        "the tax totals count separately."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        if parameters(period).gov.hmrc.stamp_duty.abolish:
            return 0
        return household("stamp_duty_land_tax", period)
