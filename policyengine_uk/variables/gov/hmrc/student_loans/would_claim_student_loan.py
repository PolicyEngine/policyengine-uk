from policyengine_uk.model_api import *


class would_claim_student_loan(Variable):
    value_type = bool
    entity = Person
    label = "Would take up a student loan if eligible"
    documentation = (
        "Whether a tertiary-educated person with no recorded student loan "
        "takes one up when the projection of later years makes them a new "
        "borrower. The dataset build assigns it once per person and stores "
        "it. It is a behavioural assumption, not an observed fact: the build "
        "applies the model's graduate take-up rate. Its situation default is "
        "false. A dataset without the column keeps the model's own draw."
    )
    definition_period = YEAR
    default_value = False
