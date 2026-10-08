from policyengine_uk.model_api import *


class benunit_reported_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "reported benefit unit capital"
    documentation = (
        "Savings and investments of the benefit unit's adults (the claimant "
        "and any partner) as recorded, such as the Family Resources Survey's "
        "benefit-unit total (TOTCAPB4). It is an input that records what was "
        "observed; each means test derives its own capital from it "
        "(uc_reported_capital, pension_credit_reported_capital). Any negative "
        "value, including the default -1, means none is recorded, and each "
        "means test falls back to its household capital proxy. 0 records no "
        "capital."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    default_value = -1
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
