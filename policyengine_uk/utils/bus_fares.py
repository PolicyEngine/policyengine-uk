"""Identify supplied bus journeys and annualise nonlinear single-fare caps."""

from policyengine_uk.utils.excise import fiscal_year_segments
from policyengine_uk.utils.supplied_inputs import supplied_input
import numpy as np


def has_bus_journeys(person, period):
    """An explicitly supplied zero is journey data; a cached default is not."""
    return any(
        supplied_input(person, name, period) is not None
        for name in ("bus_in_london_trips", "other_local_bus_trips", "local_bus_trips")
    )


def annual_capped_fare(uncapped, schedule, year):
    """Cap each fare before day-weighting over 6 April to 5 April."""
    return sum(
        np.minimum(uncapped, max(rates.cap, 0)) * share
        for rates, share in fiscal_year_segments(schedule, year)
    )


def single_fare_cap_change(fares, shares, schedule, reference, year):
    """Mean change in the price of a single ticket over the fiscal year when
    the cap follows ``schedule`` instead of ``reference``. Each uncapped fare
    is capped under both and weighted by its share of single tickets."""
    return sum(
        share
        * (
            annual_capped_fare(fare, schedule, year)
            - annual_capped_fare(fare, reference, year)
        )
        for fare, share in zip(fares, shares)
    )
