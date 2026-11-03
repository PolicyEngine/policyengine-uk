from policyengine_uk.model_api import *


class expected_ltt(Variable):
    label = "Land Transaction Tax (expected)"
    documentation = (
        "Expected annual Land Transaction Tax on the household's own property "
        "purchases and leases in Wales. land_transaction_tax is already an "
        "annual amount: it charges the prices of properties bought in the "
        "year (on the FRS-based datasets, only households in the seeded "
        "annual purchaser draw have a main-residence purchase) and the tax "
        "on each year's addition to cumulative rent. So this is "
        "land_transaction_tax with no further scaling."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["land_transaction_tax"]
