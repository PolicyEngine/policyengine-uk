from policyengine_uk.model_api import *


class targeted_childcare_entitlement_hours(Variable):
    value_type = float
    entity = BenUnit
    label = "targeted childcare entitlement hours per year"
    documentation = "Number of free childcare hours per year the benefit unit is entitled to"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        # Get age eligibility status for targeted entitlement
        targeted_eligible_age = benunit(
            "targeted_childcare_entitlement_eligibility", period
        )

        # Get eligibility status for targeted entitlement
        targeted_eligible = benunit(
            "targeted_childcare_entitlement_combine_benefits",  # Changed this line
            period,
        )

        # Use hours directly from parameters file
        p = parameters(period).gov.dwp.targeted_childcare_entitlement

        # Return hours if either eligible, 0 if not
        return where(
            targeted_eligible_age | targeted_eligible, p.hours_per_year, 0
        )
