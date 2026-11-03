from policyengine_uk.model_api import *


class housing_service_charges(Variable):
    value_type = float
    entity = Household
    label = "housing service charges"
    documentation = (
        "Annual ground rent and property service charges, including regular "
        "maintenance, site rent, factoring and other regular property charges. "
        "Supply amounts additional to rent, water and sewerage charges, "
        "mortgage interest and structural insurance, counting each cost once."
    )
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.lagged_average_earnings"
