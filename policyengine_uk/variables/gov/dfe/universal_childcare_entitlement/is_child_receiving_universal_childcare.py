from policyengine_uk.model_api import *
from policyengine_uk.utils.childcare import (
    universal_childcare_terms,
    uses_legacy_childcare_inputs,
)


class is_child_receiving_universal_childcare(Variable):
    value_type = bool
    entity = Person
    label = "child is receiving universal childcare entitlement"
    definition_period = YEAR
    documentation = (
        "A positive universal award in at least one native eligible term, "
        "including a term after a birthday later than the annual age "
        "snapshot. The existing upper-age guard remains. Genuinely supplied "
        "legacy annual shares or amounts retain the original snapshot-age "
        "predicate, without an inferred allocation to individual terms."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/2147/regulation/3",
        "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026",
    )

    def formula(person, period, parameters):
        # Get child's age
        age = person("age", period)

        # Get the parameters for universal childcare entitlement
        p = parameters(period).gov.dfe.universal_childcare_entitlement

        # Check if age is within eligible range
        meets_age_condition = (age >= p.age.min) & (age < p.age.max)
        if not uses_legacy_childcare_inputs(person, period):
            meets_age_condition = (age < p.age.max) & np.logical_or.reduce(
                universal_childcare_terms(person, period, parameters)
            )

        # Get the universal childcare entitlement amount
        entitlement_amount = person("universal_childcare_entitlement", period)

        # Child is eligible if:
        # 1. Age meets the condition AND
        # 2. Universal childcare entitlement amount > 0
        return meets_age_condition & (entitlement_amount > 0)
