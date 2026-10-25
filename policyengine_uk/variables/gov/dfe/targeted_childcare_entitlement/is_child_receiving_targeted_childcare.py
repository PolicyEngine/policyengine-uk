from policyengine_uk.model_api import *
from policyengine_uk.utils.childcare import (
    targeted_childcare_terms,
    uses_legacy_childcare_inputs,
)


class is_child_receiving_targeted_childcare(Variable):
    value_type = bool
    entity = Person
    label = "child is receiving targeted childcare entitlement"
    definition_period = YEAR
    documentation = (
        "A positive targeted award in at least one native eligible term. "
        "A transition year can contain targeted and universal awards in "
        "different terms. The targeted age scale remains independently "
        "reformable. Genuinely supplied legacy annual shares or amounts "
        "retain the original snapshot-age receiving predicate."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/2147/regulation/3",
        "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026",
    )

    def formula(person, period, parameters):
        # Get child's age
        age = person("age", period)

        # Get the parameters for targeted childcare entitlement age eligibility
        p = parameters(period).gov.dfe.targeted_childcare_entitlement

        # Check if age is eligible
        age_eligible = p.age_eligibility.calc(age)
        if not uses_legacy_childcare_inputs(person, period):
            age_eligible = np.logical_or.reduce(
                targeted_childcare_terms(person, period, parameters)
            )

        # Get the targeted childcare entitlement amount
        entitlement_amount = person("targeted_childcare_entitlement", period)

        # Child is eligible if:
        # 1. Age is eligible AND
        # 2. Targeted childcare entitlement amount > 0
        return age_eligible & (entitlement_amount > 0)
