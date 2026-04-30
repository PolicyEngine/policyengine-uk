# Council Tax Reduction Scheme Work Queue

Use this file to coordinate batched CTR implementation inside PolicyEngine UK.

## Batch Rules

- Each council keeps variables under `policyengine_uk/variables/gov/local_authorities/<authority>/council_tax_reduction/`.
- Each council keeps parameters under `policyengine_uk/parameters/gov/local_authorities/<authority>/council_tax_reduction/`.
- Prefer primary official council pages, committee papers, or scheme PDFs.
- Add at least one base-award test and one non-dependant, capital, or band-cap test where the scheme has that feature.
- Defer income-banded, UC-banded, and discount-grid schemes until they have separate helpers.
- Defer non-dependant couple/polygamous one-deduction aggregation until the shared helper has a tested household/benefit-unit grouping implementation.

## Current Batch

| Authority | Status | Type | Primary source |
| --- | --- | --- | --- |
| Bolton | Implemented | Legacy percent with earnings-bracket non-dependant deductions | https://www.bolton.gov.uk/downloads/file/745/bolton-council-tax-reduction-scheme |
| Lancaster | Implemented | Legacy full support with earnings-bracket non-dependant deductions | https://www.lancaster.gov.uk/assets/attach/14831/lancaster-city-council-2025-26-council-tax-support-scheme.pdf |
| Oldham | Implemented | Legacy percent with Band A cap and earnings-bracket non-dependant deductions | https://www.oldham.gov.uk/download/downloads/id/2632/council_tax_reduction_scheme_2025-26.pdf |

## Reviewed Candidate Queue

| Authority | Status | Type | Notes |
| --- | --- | --- | --- |
| St Albans | Ready | Legacy full support | 2025/26 official PDF found. |
| Crawley | Ready | Legacy full support | 2025/26 official PDF found; `GBP 9,000` capital limit. |
| Basingstoke and Deane | Ready | Legacy full support | 2025/26 and 2026/27 official PDFs found. |
| Adur | Ready | Legacy full support | 2025/26 official PDF found. |
| Worthing | Ready | Legacy full support | 2025/26 official PDF found. |
| Sefton | Needs helper check | Percent after reduction / working-age non-dep table | 2026/27 official PDF found. |
