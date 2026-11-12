from policyengine_uk.model_api import *


def price_base_date(parameters, period) -> str:
    """1 January of gov.simulation.price_base_year, as a date string.

    A reform can set the year as a float, so the formula takes its integer
    part before it builds the date.
    """
    year = int(parameters(period).gov.simulation.price_base_year)
    return f"{year:04d}-01-01"


class inflation_adjustment(Variable):
    label = "inflation multiplier to get base-year prices"
    documentation = (
        "Consumer price index on 1 January of gov.simulation.price_base_year "
        "divided by the index in the period."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(household, period, parameters):
        cpi = parameters.gov.economic_assumptions.indices.obr.consumer_price_index
        ratio = cpi(price_base_date(parameters, period)) / cpi(period)
        return household.empty_array() + ratio


class inflation_adjustment_ahc(Variable):
    label = "inflation multiplier to get base-year after housing costs prices"
    documentation = (
        "Ratio of one price index on 1 January of "
        "gov.simulation.price_base_year to the same index in the period. The "
        "formula uses consumer_price_index_ahc where that index has a value "
        "on both dates, and consumer_price_index on both dates otherwise."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(household, period, parameters):
        indices = parameters.gov.economic_assumptions.indices.obr
        base_date = price_base_date(parameters, period)
        ahc_base = indices.consumer_price_index_ahc(base_date)
        ahc_period = indices.consumer_price_index_ahc(period)
        if ahc_base is not None and ahc_period is not None:
            ratio = ahc_base / ahc_period
        else:
            cpi = indices.consumer_price_index
            ratio = cpi(base_date) / cpi(period)
        return household.empty_array() + ratio
