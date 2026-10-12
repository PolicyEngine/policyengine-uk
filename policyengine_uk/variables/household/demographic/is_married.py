from policyengine_uk.model_api import *


class is_married(Variable):
    value_type = bool
    entity = BenUnit
    label = "Married"
    documentation = (
        "Whether the benefit unit's couple are married to each other or in a "
        "civil partnership. Datasets supply this from the survey. Without "
        "that input, the calculator presumes every couple is married, since "
        "marriage cannot be told apart from cohabitation."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("is_couple", period)
