"""Derive gov.economic_assumptions.yoy_growth.obr.consumer_price_index_ahc.

DWP's HBAI deflates after-housing-costs incomes by CPI excluding rents,
maintenance and repairs, and water charges. The OBR does not forecast that
index, so this script derives it:

- Outturn years are calendar-year averages of the monthly index in ONS ad hoc
  3582, growth taken on the previous calendar year.
- Forecast years remove rents (OBR actual rents), water (Ofwat bills) and
  maintenance and repair (assumed to grow with CPI) from OBR CPI growth,
  using ONS CPI item weights rolled forward each year by relative prices.

Run ``python -m policyengine_uk.utils.create_ahc_deflator`` and copy the
``modified_cpi_yoy`` column, rounded to four decimal places, into
yoy_growth.yaml. policyengine_uk/tests/test_ahc_deflator.py checks that the
stored values match.
"""

import pandas as pd
import numpy as np

from policyengine_uk.system import system

# Source: ONS ad hoc 3582, Consumer Price Indices series excluding rents,
# maintenance repairs and water charges: February 2007 to June 2026 (Table 1,
# 2015=100). Calendar-year averages of the monthly index; growth is on the
# previous calendar-year average (2021 average: 111.1167).
historical_modified_cpi = pd.DataFrame(
    {
        "period": ["2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"],
        "modified_cpi_index": [121.4167, 131.4417, 135.7417, 139.3417],
        "modified_cpi_yoy": [0.0927, 0.0826, 0.0327, 0.0265],
    }
)

# Source: ONS Consumer price inflation, updating weights: Annex A, Tables W1 to W3
initial_weights = {
    "w_water": 9.7399 / 1000,
    "w_rent": 81.4551 / 1000,
    "w_repair": 2.9902 / 1000,
}

cpi = system.parameters.gov.economic_assumptions.indices.obr.consumer_price_index
water_index = system.parameters.gov.economic_assumptions.indices.ofwat.water_bills
rent_index = system.parameters.gov.economic_assumptions.indices.obr.rent


def get_parameter_values(param, start_year, end_year):
    values = {}
    for year in range(start_year, end_year + 1):
        instant = f"{year}-01-01"
        value = param(instant)
        if value is not None:
            values[year] = value
    return values


def create_modified_cpi_forecast(
    cpi_parameter,
    water_index_parameter,
    rent_index_parameter,
    historical_modified_cpi,
    initial_weights,
    forecast_start_year=2026,
    forecast_end_year=2031,
):
    cpi_values = get_parameter_values(
        cpi_parameter, forecast_start_year, forecast_end_year
    )
    water_values = get_parameter_values(
        water_index_parameter, forecast_start_year, forecast_end_year
    )
    rent_values = get_parameter_values(
        rent_index_parameter, forecast_start_year, forecast_end_year
    )

    last_historical_year = forecast_start_year - 1
    last_cpi = cpi_parameter(f"{last_historical_year}-01-01")
    last_water = water_index_parameter(f"{last_historical_year}-01-01")
    last_rent = rent_index_parameter(f"{last_historical_year}-01-01")

    results = []
    for _, row in historical_modified_cpi.iterrows():
        results.append(
            {
                "period": row["period"],
                "modified_cpi_index": row["modified_cpi_index"],
                "modified_cpi_yoy": row["modified_cpi_yoy"],
                "data_type": "historical",
            }
        )

    last_historical = historical_modified_cpi.iloc[-1]
    last_modified_index = last_historical["modified_cpi_index"]

    current_weights = initial_weights.copy()
    current_weights["w_other"] = 1 - (
        current_weights["w_water"]
        + current_weights["w_repair"]
        + current_weights["w_rent"]
    )

    forecast_years = sorted(cpi_values.keys())
    prev_cpi = last_cpi
    prev_water_index = last_water
    prev_rent_index = last_rent

    for year in forecast_years:
        current_cpi = cpi_values[year]
        current_water_index = water_values.get(year)
        current_rent_index = rent_values.get(year)

        pi_total = (current_cpi / prev_cpi) - 1
        pi_repair = pi_total  # Use CPI for maintenance and repair
        pi_water = (current_water_index / prev_water_index) - 1
        pi_rent = (current_rent_index / prev_rent_index) - 1

        housing_contribution = (
            current_weights["w_water"] * pi_water
            + current_weights["w_repair"] * pi_repair
            + current_weights["w_rent"] * pi_rent
        )

        pi_other = (pi_total - housing_contribution) / current_weights["w_other"]

        new_modified_index = last_modified_index * (1 + pi_other)

        if len(results) >= 1:
            prev_year_value = results[-1]["modified_cpi_index"]
            modified_cpi_yoy = (new_modified_index / prev_year_value) - 1
        else:
            modified_cpi_yoy = np.nan

        results.append(
            {
                "period": f"{year}-01-01",
                "year": int(year),
                "modified_cpi_index": new_modified_index,
                "modified_cpi_yoy": modified_cpi_yoy,
                "original_cpi_yoy": pi_total,
                "data_type": "forecast",
                "pi_other": pi_other,
                "pi_total": pi_total,
                "pi_rent": pi_rent,
                "pi_water": pi_water,
                "pi_repair": pi_repair,
            }
        )

        total_weighted_growth = (
            current_weights["w_water"] * (1 + pi_water)
            + current_weights["w_rent"] * (1 + pi_rent)
            + current_weights["w_repair"] * (1 + pi_repair)
            + current_weights["w_other"] * (1 + pi_other)
        )

        current_weights["w_water"] = (
            current_weights["w_water"] * (1 + pi_water) / total_weighted_growth
        )
        current_weights["w_rent"] = (
            current_weights["w_rent"] * (1 + pi_rent) / total_weighted_growth
        )
        current_weights["w_repair"] = (
            current_weights["w_repair"] * (1 + pi_repair) / total_weighted_growth
        )
        current_weights["w_other"] = (
            current_weights["w_other"] * (1 + pi_other) / total_weighted_growth
        )

        last_modified_index = new_modified_index
        prev_cpi = current_cpi
        prev_water_index = current_water_index
        prev_rent_index = current_rent_index

    return pd.DataFrame(results)


if __name__ == "__main__":
    modified_cpi_forecast = create_modified_cpi_forecast(
        cpi, water_index, rent_index, historical_modified_cpi, initial_weights
    )
    print(modified_cpi_forecast.to_string(index=False))
