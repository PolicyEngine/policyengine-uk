# Council Tax Reduction Scheme Work Queue

Use this file to coordinate batched CTR implementation inside PolicyEngine UK.

## Batch Rules

- Each council keeps variables under `policyengine_uk/variables/gov/local_authorities/<authority>/council_tax_reduction/`.
- Each council keeps parameters under `policyengine_uk/parameters/gov/local_authorities/<authority>/council_tax_reduction/`.
- Prefer primary official council pages, committee papers, or scheme PDFs.
- Add at least one base-award test and one non-dependant, capital, or band-cap test where the scheme has that feature.
- Defer broad income-banded and discount-grid schemes until they have separate helpers.
- Non-dependant couple/polygamous one-deduction aggregation is supported for benefit-unit couples by counting the highest deduction for the non-dependant benefit unit, based on joint benefit-unit earnings where the scheme uses earnings brackets. Where the source excludes Universal Credit awards from that one-deduction rule, set `one_deduction_for_uc_couples=False`.

## Current Batch

| Authority | Status | Type | Primary source |
| --- | --- | --- | --- |
| Bolton | Implemented | Legacy percent with earnings-bracket non-dependant deductions | https://www.bolton.gov.uk/downloads/file/745/bolton-council-tax-reduction-scheme |
| Lancaster | Implemented | Legacy full support with earnings-bracket non-dependant deductions | https://www.lancaster.gov.uk/assets/attach/14831/lancaster-city-council-2025-26-council-tax-support-scheme.pdf |
| Oldham | Implemented | Legacy percent with Band A cap and earnings-bracket non-dependant deductions | https://www.oldham.gov.uk/download/downloads/id/2632/council_tax_reduction_scheme_2025-26.pdf |
| Basingstoke and Deane | Implemented | Legacy full support with 2026/27 earnings-bracket non-dependant deductions | https://www.basingstoke.gov.uk/content/page/77332/Basingstoke%20S13A%202026%20Scheme%20Final.pdf |
| Crawley | Implemented | Legacy full support with `GBP 9,000` capital limit and local non-dependant schedule | https://crawley.gov.uk/sites/default/files/2025-02/Council%20Tax%20Reduction%20scheme%202025%20to%202026.pdf |
| St Albans | Implemented | Legacy full support plus Universal Credit earnings-band contribution table | https://www.stalbans.gov.uk/sites/default/files/attachments/St%20Albans%20S13A%20202526%20Final.pdf |
| Adur | Implemented | Legacy full support with 2026/27 earnings-bracket non-dependant deductions | https://www.adur-worthing.gov.uk/media/Media,174007,smxx.pdf |
| Worthing | Implemented | Legacy full support with 2026/27 earnings-bracket non-dependant deductions | https://www.adur-worthing.gov.uk/media/Media,174008,smxx.pdf |
| Sefton | Implemented | Legacy 84 percent with `GBP 6,000` capital limit and remunerative-work non-dependant table | https://www.sefton.gov.uk/media/occbaemk/ctr-scheme-2026-27.pdf |

## Reviewed Candidate Queue

| Authority | Status | Type | Notes |
| --- | --- | --- | --- |
