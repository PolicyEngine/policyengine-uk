from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.


class childcare_expenses(Variable):
    value_type = float
    entity = Person
    label = "childcare consumption"
    documentation = "Total amount spent on childcare"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
