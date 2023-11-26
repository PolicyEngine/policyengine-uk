# Data

This folder contains data files used in policy computations that are too granular for YAML parameters to be efficient.

## brma_to_region.csv.gz

This mapping file is used to convert BRMA codes to region codes. It was created by GPT-4 (20 randomly checked and all correct) for English BRMAs; Scottish, Welsh and Northern Ireland BRMAs were added manually.

## local_housing_allowance_list_of_rents.csv.gz

This file contains the list of rents used to determine LHA rates. English BRMAs for 2019 and 2020 are from the Valuation Office Agency [here](https://www.gov.uk/government/collections/local-housing-allowance-list-of-rents). Scottish, Welsh and Northern Ireland BRMAs are matched from the closest English BRMA.
