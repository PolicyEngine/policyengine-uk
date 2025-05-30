from policyengine_uk.model_api import *
import pandas as pd


class MaritalStatus(Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    SEPARATED = "Separated"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"


class marital_status(Variable):
    value_type = Enum
    possible_values = MaritalStatus
    default_value = MaritalStatus.SINGLE
    entity = Person
    label = "Marital status"
    definition_period = YEAR

    def formula(person, period, parameters):
        return where(
            person.benunit("is_married", period),
            MaritalStatus.MARRIED,
            MaritalStatus.SINGLE,
        )
