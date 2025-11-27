from policyengine_uk.model_api import *


class rail_subsidy_spending(Variable):
    label = "rail subsidy spending"
    documentation = (
        "Total spending on rail subsidies for this household. "
        "Uprated by regulated rail fare increases (RPI + 1% formula)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.dft.rail.regulated_fare_increase"
