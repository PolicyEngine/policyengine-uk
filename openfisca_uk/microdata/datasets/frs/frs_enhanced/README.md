# Enhanced FRS

This folder contains the definition of the enhanced FRS dataset, which imputes data from:
* The Living Costs and Food Survey (consumption)
* The Wealth and Assets Survey (assets)
onto the Family Resources Survey (income).

## LCF Imputations

The LCF dataset contains consumption data, but not carbon emissions. To estimate carbon emissions, we use [official estimates of the UK's carbon footprint](https://www.gov.uk/government/statistics/uks-carbon-footprint). These estimate the carbon emissions produced by each category of consumption. `ncfs_emissions_2019.csv` contains these estimates for 2019, along with their category names and [COICOP codes](https://unstats.un.org/unsd/classifications/unsdclassifications/COICOP_2018_-_pre-edited_white_cover_version_-_2018-12-26.pdf).

## WAS Imputations

The WAS dataset contains measures of property and corporate wealth, which we use to estimate the total land value tax exposure.
