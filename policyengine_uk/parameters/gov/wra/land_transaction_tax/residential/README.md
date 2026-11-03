# Residential Land Transaction Tax

The scales apply marginal rates to the consideration for each purchase. The
main and additional-property purchase inputs select the main and higher tables
respectively; the final Land Transaction Tax charge applies only in Wales.

[WSI 2022/1027, regulation 7](https://www.legislation.gov.uk/wsi/2022/1027/regulation/7/made)
replaced the main residential table from 10 October 2022:

| Portion of consideration | Rate |
| --- | ---: |
| Up to £225,000 | 0% |
| Over £225,000 to £400,000 | 6% |
| Over £400,000 to £750,000 | 7.5% |
| Over £750,000 to £1,500,000 | 10% |
| Over £1,500,000 | 12% |

[WSI 2024/1311, regulation 6](https://www.legislation.gov.uk/wsi/2024/1311/regulation/6/made)
replaced the higher residential table from 11 December 2024:

| Portion of consideration | Rate |
| --- | ---: |
| Up to £180,000 | 5% |
| Over £180,000 to £250,000 | 8.5% |
| Over £250,000 to £400,000 | 10% |
| Over £400,000 to £750,000 | 12.5% |
| Over £750,000 to £1,500,000 | 15% |
| Over £1,500,000 | 17% |

The raw parameter files retain these statutory dates and the preceding history.
The annual model samples transactional parameters on 30 April. Therefore the
main table changes in model year 2023, while the higher table changes in model
year 2025. Model years 2022 and 2024 retain their respective April tables;
neither year blends the old and new rates.

The annual Household purchase inputs have no transaction date, contract date,
election or subsequent-contract-event fields. They cannot select a transaction
later in the change year or model protected old contracts. Under
[the 2022 regulations, regulations 4–6](https://www.legislation.gov.uk/wsi/2022/1027/made),
qualifying earlier contracts require an election which must not increase tax.
Under [the 2024 regulations, regulations 4–5](https://www.legislation.gov.uk/wsi/2024/1311/made),
qualifying earlier contracts are protected without an election requirement.
Both provisions have conditions and exclusions; an earlier contract alone is
not sufficient in every case. These transaction-specific provisions are outside
the annual input contract.
