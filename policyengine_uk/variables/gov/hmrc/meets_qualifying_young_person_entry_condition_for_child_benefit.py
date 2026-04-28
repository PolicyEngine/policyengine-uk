from policyengine_uk.model_api import *


class meets_qualifying_young_person_entry_condition_for_child_benefit(Variable):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person entry condition for Child Benefit"
    definition_period = YEAR
    reference = "https://www.gov.uk/hmrc-internal-manuals/child-benefit-technical-manual/cbtm07020"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.child_benefit.eligibility
        age = person("age", period)
        entry_age = person(
            "age_started_or_accepted_current_education_or_training", period
        )
        return (age < p.education_or_training_start_age_limit) | (
            entry_age < p.education_or_training_start_age_limit
        )
