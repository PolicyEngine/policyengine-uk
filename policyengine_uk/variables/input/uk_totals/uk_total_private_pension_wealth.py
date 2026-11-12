from policyengine_uk.model_api import *


class uk_total_private_pension_wealth(Variable):
    label = "UK total of private pension wealth"
    documentation = (
        "private_pension_wealth summed over all UK households at their weights, the "
        "same on every household. Whoever holds the whole population "
        "supplies it (policyengine_uk.utils.uk_totals.add_uk_totals), so that "
        "a simulation of part of the UK gives each household its share of "
        "the UK total of corporate_sector_wealth. 0 where not supplied."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.uk_totals.per_capita_gdp"
