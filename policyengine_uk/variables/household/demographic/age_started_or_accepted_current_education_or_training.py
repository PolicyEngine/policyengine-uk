from policyengine_uk.model_api import *


class age_started_or_accepted_current_education_or_training(Variable):
    value_type = float
    entity = Person
    label = "Age when current education or training started or was accepted"
    documentation = (
        "The age at which this person started, enrolled on, or was accepted "
        "onto their current education or training."
    )
    definition_period = YEAR
    default_value = 1000
