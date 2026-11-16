"""Derive gov.economic_assumptions.yoy_growth.ofwat.water_bills.

Each value is nominal growth in the average household water and sewerage bill
in England and Wales for the charging year starting in April, so 2027-01-01
holds 2027-28.

- 2022-2024: Ofwat average bills in real terms, converted to nominal with CPIH
  (``historical_growth``).
- 2025-2026: published outturn, stored directly in yoy_growth.yaml and read
  from there.
- 2027-2029: the PR24 final determinations (Ofwat, 19 December 2024) set the
  average water and wastewater company bill at GBP 440 in 2024-25 and GBP 597
  in 2029-30, before inflation (pr24_final_determination_bills.csv). The real
  growth already realised in 2025-26 and 2026-27 is taken out, the rest is
  spread evenly over 2027-28 to 2029-30, and CPIH is added back
  (``projected_growth``).

Inflation: Ofwat indexes price limits to CPIH in the November before the
charging year. The repo holds calendar-year CPIH growth
(``yoy_growth.obr.cpih``), so charging year t uses calendar year t-1 as the
nearest match.

Run ``python -m policyengine_uk.utils.water.forecast_water_bills`` and copy
the rounded values into yoy_growth.yaml.
policyengine_uk/tests/test_water_bills_growth.py checks the stored values
match.
"""

from pathlib import Path

import pandas as pd

from policyengine_uk.system import system

FINAL_DETERMINATION_BILLS = Path(__file__).parent / "pr24_final_determination_bills.csv"
INDUSTRY_AVERAGE_ROW = "water_and_wastewater_average"
FINAL_DETERMINATION_START_YEAR = 2024
FINAL_DETERMINATION_END_YEAR = 2029
FIRST_PROJECTED_YEAR = 2027
DECIMALS = 3

GROWTH = system.parameters.gov.economic_assumptions.yoy_growth
WATER_BILLS = GROWTH.ofwat.water_bills
CPIH = GROWTH.obr.cpih


def historical_growth() -> dict[int, float]:
    """Nominal growth for 2022-2024 from Ofwat real bills and CPIH."""
    df = pd.DataFrame(
        {
            "year": [2021, 2022, 2023, 2024],
            "real_bill": [486, 470, 486, 492],
            "cpih": [113.1, 123.0, 129.9, 134.0],
        }
    )
    nominal = df["real_bill"] * df["cpih"] / 100
    nominal = (nominal / nominal.iloc[0] * 100).round(1)
    growth = nominal.pct_change().round(DECIMALS)
    return dict(zip(df["year"].iloc[1:], growth.iloc[1:]))


def final_determination_real_growth() -> float:
    """Real growth in the average bill from 2024-25 to 2029-30."""
    bills = pd.read_csv(FINAL_DETERMINATION_BILLS)
    average = bills[bills["company_type"] == INDUSTRY_AVERAGE_ROW].iloc[0]
    return average["bill_2029_30"] / average["bill_2024_25"]


def charging_year_inflation(year: int) -> float:
    return CPIH(f"{year - 1}-01-01")


def projected_growth() -> dict[int, float]:
    """Nominal growth for 2027-2029, unrounded."""
    realised = 1.0
    for year in range(FINAL_DETERMINATION_START_YEAR + 1, FIRST_PROJECTED_YEAR):
        nominal = WATER_BILLS(f"{year}-01-01")
        realised *= (1 + nominal) / (1 + charging_year_inflation(year))
    remaining_years = FINAL_DETERMINATION_END_YEAR - FIRST_PROJECTED_YEAR + 1
    real_per_year = (final_determination_real_growth() / realised) ** (
        1 / remaining_years
    )
    return {
        year: real_per_year * (1 + charging_year_inflation(year)) - 1
        for year in range(FIRST_PROJECTED_YEAR, FINAL_DETERMINATION_END_YEAR + 1)
    }


def project_water_bills() -> pd.DataFrame:
    rows = [
        {"year": year, "growth": growth, "source": "Ofwat real bills and CPIH"}
        for year, growth in historical_growth().items()
    ]
    rows += [
        {
            "year": year,
            "growth": WATER_BILLS(f"{year}-01-01"),
            "source": "published (stored)",
        }
        for year in range(FINAL_DETERMINATION_START_YEAR + 1, FIRST_PROJECTED_YEAR)
    ]
    rows += [
        {
            "year": year,
            "growth": round(growth, DECIMALS),
            "source": "PR24 final determinations and OBR CPIH",
        }
        for year, growth in projected_growth().items()
    ]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print(project_water_bills().to_string(index=False))
