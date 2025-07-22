from policyengine_uk.model_api import *


class is_child_for_CTC(Variable):
    value_type = bool
    entity = Person
    label = "Child eligible for Child Tax Credit"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 8"

    def formula(person, period, parameters):
        return person("is_child_or_QYP", period)
