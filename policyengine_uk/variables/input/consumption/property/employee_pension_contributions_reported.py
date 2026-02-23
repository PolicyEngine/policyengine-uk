from policyengine_uk.model_api import *


class employee_pension_contributions_reported(Variable):
    label = "employee pension contributions (reported)"
    documentation = (
        "The reported employee pension contributions from survey data, "
        "before any adjustments for salary sacrifice cap reforms. "
        "Note: This variable is populated from the 'employee_pension_contributions' "
        "field in the microdata via input aliasing."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.average_earnings"
