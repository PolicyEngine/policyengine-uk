from policyengine_uk.system import system

# Run this script to generate the triple lock parameter for updated CPI and average earnings forecasts from the OBR.

cpi = (
    system.parameters.gov.economic_assumptions.indices.obr.consumer_price_index
)
average_earnings = (
    system.parameters.gov.economic_assumptions.indices.obr.average_earnings
)

START_YEAR = 2021

triple_lock = system.parameters.gov.dwp.state_pension.triple_lock
lock_value = triple_lock(START_YEAR - 1)

for year in range(START_YEAR, 2029):
    earnings_increase = average_earnings(year - 1) / average_earnings(year - 2)
    cpi_increase = cpi(year - 1) / cpi(year - 2)
    triple_lock_increase = max(earnings_increase, cpi_increase, 1.025)
    lock_value *= triple_lock_increase
    print(
        f"  {year}-01-01: {lock_value:.3f} # Earnings increase FY{year - 1}/{year - 2} = {earnings_increase - 1:.1%}, CPI increase FY{year - 1}/{year - 2} = {cpi_increase - 1:.1%}"
    )
