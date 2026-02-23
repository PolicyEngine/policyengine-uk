from policyengine_uk.model_api import *


class is_scp_eligible_child(Variable):
    label = "Eligible for Scottish Child Payment"
    documentation = "Whether this child is eligible for Scottish Child Payment based on age."
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.social_security_scotland.scottish_child_payment
        age = person("age", period)
        max_age = p.max_age
        return age < max_age
