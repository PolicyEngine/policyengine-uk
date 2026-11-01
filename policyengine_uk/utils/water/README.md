# Water bills projections

In this folder, we have:

* `forecast_water_bills.py` - derives `gov.economic_assumptions.yoy_growth.ofwat.water_bills`. Run `python -m policyengine_uk.utils.water.forecast_water_bills` and copy the 2027-2029 values into `yoy_growth.yaml`; `policyengine_uk/tests/test_water_bills_growth.py` checks they match.
* `pr24_final_determination_bills.csv` - average household bills in 2024-25 and 2029-30, before inflation, for each water company and the weighted averages, from page 21 of Ofwat's [PR24 final determinations sector summary](https://www.ofwat.gov.uk/wp-content/uploads/2024/12/PR24-FD-sector-summary-revised.pdf) (19 December 2024; the PDF downloaded on 23 October 2026 had sha256 `4207ea63d3489ae60a052746bdef105f6f52c7cc21f84f492238adf43c95b9cd`). The script uses the published weighted average for water and wastewater companies, so no customer numbers are needed. The per-company rows are kept for reference.

After changing the water bill values, rerun `python -m policyengine_uk.utils.create_ahc_deflator` and update `obr.consumer_price_index_ahc`, which removes water charges from CPI.
