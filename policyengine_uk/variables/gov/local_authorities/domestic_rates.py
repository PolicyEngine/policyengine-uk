from policyengine_uk.model_api import *


class domestic_rates(Variable):
    label = "domestic rates"
    documentation = (
        "Annual domestic rates bill of a Northern Ireland household: the "
        "regional rate plus its council's district rate, levied on the "
        "dwelling's capital value as one bill (Rates (Northern Ireland) "
        "Order 1977, arts 6 and 9). Supplied by the dataset rather than "
        "computed; projected years grow it by "
        "gov.economic_assumptions.yoy_growth.finance_ni.domestic_rates."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
