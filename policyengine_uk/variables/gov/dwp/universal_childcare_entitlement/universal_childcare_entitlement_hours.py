from policyengine_uk.model_api import *


class universal_childcare_entitlement_hours(Variable):
    value_type = float
    entity = BenUnit
    label = "universal childcare entitlement hours per year"
    documentation = (
        "Number of free childcare hours per year the benefit unit is entitled to"
    )
    definition_period = YEAR
    unit = "hour"

    def formula(benunit, period, parameters):
        """
        Calculate number of free hours the benefit unit is entitled to.

        Args:
            benunit: The benefit unit
            period: The time period
            parameters: Policy parameters

        Returns:
            float: Number of free childcare hours per year
        """
        # Get eligibility status
        is_eligible = benunit("universal_childcare_entitlement_eligibility", period)

        # Use hours directly from parameters file
        hours = parameters(
            period
        ).gov.dwp.universal_childcare_entitlement.hours_per_year

        # Return hours if eligible, 0 if not
        return where(is_eligible, hours, 0)
