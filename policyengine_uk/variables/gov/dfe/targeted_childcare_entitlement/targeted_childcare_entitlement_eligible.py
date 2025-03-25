from policyengine_uk.model_api import *


class targeted_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligibility for targeted childcare entitlement"
    definition_period = YEAR

    def formula(benunit, period, parameters):

        # Check if household is in England
        country = benunit.household("country", period)
        in_england = country == country.possible_values.ENGLAND

        # Get parameters
        p = parameters(period).gov.dfe.targeted_childcare_entitlement

        # Check if household receives any qualifying benefits
        has_qualifying_benefits = (
            add(benunit, period, p.qualifying_benefits) > 0
        )

        # Check if household meets any additional qualifying criteria
        # from qualifying_criteria.yaml (UC/TC specific criteria)
        meets_any_criteria = add(benunit, period, p.qualifying_criteria) > 0
        return in_england & (has_qualifying_benefits | meets_any_criteria)
