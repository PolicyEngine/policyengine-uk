from policyengine_uk.model_api import *


class parents_learning_allowance(Variable):
    value_type = float
    entity = Person
    label = "Parents' Learning Allowance"
    documentation = (
        "Student Finance England Parents' Learning Allowance for students with dependent children. "
        "GOV.UK publishes the maximum award and the household-income cutoff, but not a simple public award curve. "
        "This first-pass model therefore pays the published maximum amount to eligible students rather than "
        "inventing a taper."
    )
    definition_period = YEAR
    quantity_type = FLOW
    unit = GBP
    defined_for = "parents_learning_allowance_eligible"

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.parents_learning_allowance
        return p.maximum
