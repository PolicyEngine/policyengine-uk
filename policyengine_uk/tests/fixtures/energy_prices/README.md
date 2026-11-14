# Real energy price source fixtures

The importer `policyengine_uk/utils/import_energy_prices.py` reads these and
must reproduce `ons.yaml`, `obr.yaml` and `consumption_shares.yaml` under
`policyengine_uk/parameters/gov/economic_assumptions/energy_prices` byte for
byte. No test downloads a source file.

- `mm23_energy_columns.csv`: the row label column and the D7DT, D7DU, DK9U,
  CJXA, CJXB and A9F4 columns of ONS MM23 (consumer price inflation time
  series), every row, released 21 October 2026 (to September 2026). Other
  columns are dropped; the cells kept are unchanged. Source:
  <https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/datasets/consumerpriceindices/current/mm23.csv>,
  SHA-256 of the full file
  `ed5b20bea47cda76f38519c17d4c48f7d2b003aad5b3c69aa8f4d4f805f6ebc1`.
- `efo_october_2026_economy_table_1_19.xlsx`: the Contents and 1.19 (CPI
  category inflation) worksheets of the OBR October 2026 EFO detailed forecast
  tables, economy (`efo-october-2026-detailed-forecast-tables-economy.xlsx`,
  SHA-256 `96795d1747bb5a4978c7fb768689d5fd31f568e5223db8a94b1bd92ba7f6c118`).
  Source: <https://obr.uk/efo/economic-and-fiscal-outlook-october-2026/>.
- `ET_5.2_SEP_26_quarter.xlsx`: the Quarter worksheet of DESNZ Energy Trends
  table ET 5.2, September 2026 (`ET_5.2_SEP_26.xlsx`, SHA-256
  `f3055161b08365a959af349a3d587056b8e9afaf21c0b087986bd204d8ca65c8`).
  Source: <https://www.gov.uk/government/statistics/electricity-section-5-energy-trends>.
- `ET_4.1_SEP_26_quarter_gwh.xlsx`: the Quarter (GWh) worksheet of DESNZ
  Energy Trends table ET 4.1, September 2026 (`ET_4.1_SEP_26.xlsx`, SHA-256
  `3b40e0858ad75ede9fc671c00a1a3bd9a59df8640df504acf54b3afc22301c7c`).
  Source: <https://www.gov.uk/government/statistics/gas-section-4-energy-trends>.

In each workbook only the sheet list and relationships were reduced to those
worksheets; the worksheet XML and shared strings are the originals. They are
minimal archives for the importer's XLSX reader, not complete Excel files.
