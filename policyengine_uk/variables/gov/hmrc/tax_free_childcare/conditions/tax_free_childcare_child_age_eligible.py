from policyengine_uk.model_api import *


class tax_free_childcare_child_age_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible child for the tax-free childcare"
    definition_period = YEAR

    def formula(person, period, parameters):
        # Get person's characteristics
        age = person("age", period)

        # Get age thresholds from parameters
        p = parameters(period).gov.hmrc.tax_free_childcare.age

        # Check disability status
        is_disabled = person("is_disabled_for_benefits", period)
        is_blind = person("is_blind", period)

        # Determine age limit based on disability status
        age_limit = where(is_disabled | is_blind, p.disability, p.standard)
        return age < age_limit
