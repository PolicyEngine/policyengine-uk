from policyengine_uk.model_api import *


class universal_free_childcare_hours(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal free childcare hours per year"
    documentation = (
        "Number of free childcare hours per year the benefit unit is entitled to "
        "under the universal offer for 3-4 year olds"
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
        is_eligible = benunit("universal_free_childcare_eligibility", period)

        # Use hours directly from parameters file
        hours = parameters(
            period
        ).gov.dwp.childcare_subsidies.universal_free_childcare.hours_per_year_universal_free_childcare

        # Return hours if eligible, 0 if not
        return where(is_eligible, hours, 0)
