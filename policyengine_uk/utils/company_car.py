"""Inputs of the company car and car fuel benefits, as the formulas read them."""

from policyengine_core.model_api import max_, min_, where
import numpy as np


def co2_emissions_figure(person, period):
    """The company car's CO2 emissions figure for ITEPA 2003 s. 139.

    Rounded down to a whole number (s. 139(2)(a)). A car of the ELECTRIC
    fuel type (electric or other zero emission) is taken to have a figure of
    0 whatever CO2 figure is entered, as for vehicle excise duty, so a car is
    zero-emission for both the appropriate percentage and the car fuel
    benefit (s. 149(4)) exactly when this is 0.
    """
    fuel_type = person("company_car_fuel_type", period)
    co2 = np.floor(max_(person("company_car_co2_emissions", period), 0))
    return where(fuel_type == fuel_type.possible_values.ELECTRIC, 0, co2)


def share_of_year_available(person, period):
    """The share of the tax year the company car is available, from 0 to 1.

    Both benefits are reduced in proportion to the days the car is
    unavailable (ITEPA 2003 ss. 143(3) and 152(1)).
    """
    return min_(max_(person("company_car_availability", period), 0), 1)
