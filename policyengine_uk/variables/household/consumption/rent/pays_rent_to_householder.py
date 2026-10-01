from policyengine_uk.model_api import *


class pays_rent_to_householder(Variable):
    value_type = bool
    entity = Person
    label = "Family pays rent to the householder"
    documentation = (
        "Whether any member of this person's benefit unit pays the "
        "householder rent as a boarder or lodger."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        payments = add(person, period, ["rent_paid_as_boarder", "rent_paid_as_lodger"])
        return person.benunit.any(payments > 0)
