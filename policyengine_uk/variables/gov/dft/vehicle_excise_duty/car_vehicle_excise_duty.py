import numpy as np

from policyengine_uk.model_api import *


class car_vehicle_excise_duty(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = GBP
    label = "Vehicle excise duty on this person's car"
    reference = "https://www.legislation.gov.uk/ukpga/1994/22/schedule/1"

    def formula_2024(person, period, parameters):
        p = parameters(period).gov.dft.vehicle_excise_duty
        registration = person("car_first_registration_date", period)
        emissions = max_(person("car_co2_emissions", period), 0)
        engine = person("car_engine_size", period)
        price = person("car_list_price", period)
        fuel = person("car_fuel_type", period)
        fuel_types = fuel.possible_values
        zero_emission = fuel == fuel_types.ELECTRIC
        emissions = where(zero_emission, 0, emissions)
        alternative = fuel == fuel_types.ALTERNATIVE_FUEL

        # One twelve-month licence per VED rate year (1 April to 31 March),
        # with uninterrupted annual renewals since first registration.
        year_start = np.datetime64(f"{period.start.year}-04-01")
        year_end = np.datetime64(f"{period.start.year + 1}-04-01")
        registration_year = registration.astype("datetime64[Y]")
        registration_month = registration.astype("datetime64[M]")
        april = registration_year.astype("datetime64[M]") + np.timedelta64(3, "M")
        licence_year = (
            year_start.astype("datetime64[Y]").astype(int)
            - registration_year.astype(int)
            + (registration_month < april)
        )
        modern = registration >= np.datetime64(date(*p.modern_registration_start))
        graduated = registration >= np.datetime64(date(*p.graduated_registration_start))
        first_year_rate = where(
            fuel == fuel_types.DIESEL_NON_RDE2,
            p.first_year_diesel_non_rde2.calc(emissions, right=True),
            p.first_year.calc(emissions, right=True),
        )
        first_year_rate = max_(
            first_year_rate - alternative * p.alternative_fuel_discount, 0
        )
        threshold = where(
            zero_emission,
            p.zero_emission_expensive_car_threshold,
            p.expensive_car_threshold,
        )
        supplement = (
            (price > threshold)
            & (licence_year >= 1)
            & (licence_year <= p.supplement_years)
            & (
                ~zero_emission
                | (
                    registration
                    >= np.datetime64(
                        date(*p.zero_emission_supplement_registration_start)
                    )
                )
            )
        ) * p.expensive_car_supplement
        modern_rate = where(
            licence_year == 0,
            first_year_rate,
            p.standard_rate - alternative * p.alternative_fuel_discount + supplement,
        )
        graduated_emissions = where(
            registration < np.datetime64(date(*p.band_k_registration_cutoff)),
            min_(emissions, p.band_k_max_emissions),
            emissions,
        )
        graduated_rate = max_(
            p.graduated.calc(graduated_emissions, right=True)
            - alternative * p.alternative_fuel_discount,
            0,
        )
        engine_rate = where(
            (engine <= p.engine_size_threshold) | zero_emission,
            p.small_engine_rate,
            p.large_engine_rate,
        )
        charge = select(
            [modern, graduated], [modern_rate, graduated_rate], default=engine_rate
        )
        exempt = person("car_is_ved_exempt", period) | (
            zero_emission & p.zero_emission_exempt
        )
        return where((registration < year_end) & ~exempt, charge, 0)
