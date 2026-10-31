# Real OBR receipts table fixtures

These parser fixtures retain the original worksheet XML for Contents, Other
taxes (3.2, or 4.2 in October 2026), Property transactions taxes: receipts by
sector (3.7, or 4.7), Current receipts (on a cash basis: 3.9 in March 2025,
3.8 in March 2026, 4.8 in October 2026), Tobacco clearances (3.11, or 4.11),
Alcohol clearance forecasts (3.12, or 4.12, a sheet that also holds the
alcohol receipts forecasts) and, from March 2026, Betting and gaming duties
forecast breakdown (3.10, or 4.10), plus the original shared strings. The
March 2025 tables have no betting and gaming breakdown. Only the workbook's
sheet list and relationships were reduced to those entries. The published unit cells, fiscal-year headers, markers, row labels and
numeric cells are unchanged. These are minimal archives for the importer's XLSX
reader, rather than complete Excel documents with styles and charts. The
October 2026 workbook titles sheet 4.8 "43.8 Current receipts (on a cash
basis)"; the fixture keeps that misprint.

Sources: OBR [March 2025 EFO](https://obr.uk/efo/economic-and-fiscal-outlook-march-2025/),
[March 2026 EFO](https://obr.uk/efo/economic-and-fiscal-outlook-march-2026/)
and [October 2026 EFO](https://obr.uk/efo/economic-and-fiscal-outlook-october-2026/),
receipts detailed forecast tables. The original files used for extraction are
`obr_efo_march_2025_receipts.xlsx`, `obr_efo_march_2026_receipts.xlsx` and
`efo-october-2026-detailed-forecast-tables-receipts.xlsx` (in the October 2026
detailed forecast tables zip file). Their SHA-256 hashes are:

- March 2025: `6b20e05e93c50e3ccae1d3111fd84b8fa326b75c38c8ab055fad694648c75905`
- March 2026: `f65b6cb7f96931d4abd85940794eb60f6f65afca8bbf16c74a4548bf92766a28`
- October 2026: `d115705716d77b11c190385d41cb1924f30080c9331a8a386c04d4e65a368e95`

The committed YAML holds the October 2026 tables over the March 2026 ones.
Tests mutate the unit cell and selected receipt levels inside these real tables;
the unchanged control must reproduce the committed YAML byte for byte. No test
downloads a workbook or depends on a developer's local source directory.
