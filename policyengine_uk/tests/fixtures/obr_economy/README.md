# Real OBR economy table fixture

`efo_october_2026_economy_table_1_13.xlsx` holds the Contents and 1.13
(National Living Wage) worksheets of the OBR October 2026 EFO detailed
forecast tables, economy
(`efo-october-2026-detailed-forecast-tables-economy.xlsx` in the detailed
forecast tables zip file, SHA-256
`96795d1747bb5a4978c7fb768689d5fd31f568e5223db8a94b1bd92ba7f6c118`). Source:
<https://obr.uk/efo/economic-and-fiscal-outlook-october-2026/>.

As with the energy price fixtures, a script kept only those worksheets in the
workbook's sheet list and relationships, dropped its defined names, and copied
the worksheet XML and shared strings byte for byte. The archive serves the
importer's XLSX reader and leaves out the styles and other parts a full Excel
file has.

`policyengine_uk/utils/import_obr_forecasts.py` must reproduce
`obr.national_living_wage` in `yoy_growth.yaml` from it byte for byte. Tests
change cells of sheet 1.13 to check that the importer refuses a changed layout
rather than reading another row. No test downloads a workbook. With each new
EFO, replace the file with the new table and update `OBR_NATIONAL_LIVING_WAGE`
in `policyengine_uk/tests/test_minimum_wage_projection.py`, which must equal
it.
