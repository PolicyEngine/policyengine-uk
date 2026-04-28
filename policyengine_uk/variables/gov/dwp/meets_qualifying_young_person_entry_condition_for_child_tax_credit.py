from policyengine_uk.model_api import *


class meets_qualifying_young_person_entry_condition_for_child_tax_credit(Variable):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person entry condition for Child Tax Credit"
    definition_period = YEAR
    reference = "https://www.gov.uk/hmrc-internal-manuals/tax-credits-technical-manual/tctm02220"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.tax_credits.child_tax_credit.eligibility
        age = person("age", period)
        entry_age = person(
            "age_started_or_accepted_current_education_or_training", period
        )
        return (age < p.education_or_training_start_age_limit) | (
            entry_age < p.education_or_training_start_age_limit
        )
