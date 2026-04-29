from policyengine_uk.model_api import *


class adult_dependants_grant(Variable):
    value_type = float
    entity = Person
    label = "Adult Dependants' Grant"
    documentation = (
        "Student Finance England Adult Dependants' Grant. "
        "GOV.UK publishes the maximum award and income tests, but not a simple public award curve. "
        "This first-pass model therefore pays the published maximum amount to eligible students rather than "
        "inventing a taper."
    )
    definition_period = YEAR
    quantity_type = FLOW
    unit = GBP
    defined_for = "adult_dependants_grant_eligible"

    def formula(person, period, parameters):
        return parameters(period).gov.dfe.adult_dependants_grant.maximum
