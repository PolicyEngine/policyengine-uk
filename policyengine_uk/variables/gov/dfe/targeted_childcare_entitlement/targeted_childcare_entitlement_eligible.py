from policyengine_uk.model_api import *


class targeted_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligibility for targeted childcare entitlement"
    definition_period = YEAR
    defined_for = "would_claim_targeted_childcare"
    reference = "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026"

    def formula(benunit, period, parameters):
        # Check if household is in England
        country = benunit.household("country", period)
        in_england = country == country.possible_values.ENGLAND

        # Get parameters
        p = parameters(period).gov.dfe.targeted_childcare_entitlement

        # Eligibility for the working parent entitlement does not remove the
        # targeted hours: DfE's statutory guidance (April 2026, para A1.11)
        # funds the first 15 hours of a child eligible for both under Early
        # Learning for 2-year-olds, and extended_childcare_entitlement adds
        # the working parent hours above them.

        # Check if household receives any qualifying benefits
        has_qualifying_benefits = add(benunit, period, p.qualifying_benefits) > 0

        # Check if household meets any additional qualifying criteria
        # from qualifying_criteria.yaml (UC/TC specific criteria)
        meets_any_criteria = add(benunit, period, p.qualifying_criteria) > 0
        return in_england & (has_qualifying_benefits | meets_any_criteria)
