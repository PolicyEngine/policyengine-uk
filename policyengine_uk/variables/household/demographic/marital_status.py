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
    documentation = (
        "Datasets supply this from the survey. Without that input, the "
        "claimant and partner of a married benefit unit are married and "
        "everyone else, including their children, is single."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return where(
            person.benunit("is_married", period)
            & person("is_claimant_or_partner", period),
            MaritalStatus.MARRIED,
            MaritalStatus.SINGLE,
        )
