from policyengine_uk.model_api import *


class extended_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligibility for extended childcare entitlement"
    definition_period = YEAR
    defined_for = "would_claim_extended_childcare"

    def formula(benunit, period, parameters):
        # Check if household is in England
        country = benunit.household("country", period)
        countries = country.possible_values
        in_england = country == countries.ENGLAND

        # Check income condition - must be true for all family members (except children)
        person = benunit.members
        person_meets_income_condition = person(
            "extended_childcare_entitlement_meets_income_requirements",
            period,
        ) | person("is_child", period)
        meets_income_condition = benunit.all(person_meets_income_condition)

        # Check work condition
        work_eligible = (
            benunit("extended_childcare_entitlement_work_condition", period)
            > 0
        )

        return in_england & meets_income_condition & work_eligible
