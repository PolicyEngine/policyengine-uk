from policyengine_uk.model_api import *


class is_in_full_time_education(Variable):
    value_type = bool
    entity = Person
    label = "On a full-time course of education or training"
    documentation = (
        "Whether this person is undertaking a full-time course of study or "
        "training, including the vacations within the course. An input that "
        "is false unless set: no formula derives it, and a dataset that "
        "does not supply it leaves it false. It says only that the course is "
        "full-time; current_education and in_HE give its level. Universal "
        "Credit reads it for the condition that a claimant is not receiving "
        "education (uc_receiving_education)."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/12",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/13",
    )
