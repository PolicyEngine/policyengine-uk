# Local Housing Allowance

## Lists of rents

`lha_list_of_rents.csv.gz` holds one row per rent in the lists behind the April 2019 and April 2020 determinations (`year`), with its BRMA and LHA category. The model uses it only to turn the published 30th percentile into another percentile when a reform changes `percentile`.

- **England:** the Valuation Office Agency's published lists.
- **Scotland:** Rent Service Scotland's records, released by the Scottish Government under FOI 202200303624. The list for April Y is the sheet for the year to September Y-1. `scripts/build_scottish_list_of_rents.py` rebuilds these rows from the pinned workbook. In 522 of 540 cells (April 2017-2022), those sheets reproduce the published 30th percentiles to the penny.
- **Wales and Northern Ireland:** copies of English BRMAs' lists, each matched on the nation's April 2019 rate (issue #2036). Their percentile reforms use the median English ratio for the category instead.
