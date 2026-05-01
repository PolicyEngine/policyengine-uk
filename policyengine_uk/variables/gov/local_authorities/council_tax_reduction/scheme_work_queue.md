# Council Tax Reduction Scheme Work Queue

Use this file to coordinate batched CTR implementation inside PolicyEngine UK.

## Coverage Target

- England has `296` billing authorities in the 2026/27 MHCLG Council Tax tables. England pensioner CTR is national; the remaining implementation surface is working-age local schemes.
- This PR currently supports `48` current English working-age billing authorities, plus the national Wales and Scotland CTR schemes.
- Current 2026/27 billing-authority enum gaps identified from MHCLG Table 9 and added in this PR: Bristol, Cumberland, Durham, Herefordshire, Kingston upon Hull, North Northamptonshire, North Yorkshire, Somerset, West Northamptonshire, and Westmorland and Furness.
- Source for the billing-authority inventory: https://www.gov.uk/government/statistics/council-tax-levels-set-by-local-authorities-in-england-2026-to-2027

## Batch Rules

- Each council keeps variables under `policyengine_uk/variables/gov/local_authorities/<authority>/council_tax_reduction/`.
- Each council keeps parameters under `policyengine_uk/parameters/gov/local_authorities/<authority>/council_tax_reduction/`.
- Prefer primary official council pages, committee papers, or scheme PDFs.
- Add at least one base-award test and one non-dependant, capital, or band-cap test where the scheme has that feature.
- Defer broad income-banded and discount-grid schemes until they have separate helpers.
- Non-dependant couple/polygamous one-deduction aggregation is supported for benefit-unit couples by counting the highest deduction for the non-dependant benefit unit, based on joint benefit-unit earnings where the scheme uses earnings brackets. Where the source excludes Universal Credit awards from that one-deduction rule, set `one_deduction_for_uc_couples=False`.

## Batch Agent Workflow

Use three separate passes for large batches:

- Scout: find official sources, extract page/paragraph-cited facts, and classify the scheme archetype. Do not code in this pass.
- Implementer: write failing YAML tests first, then jurisdiction-scoped parameters and variables. Work from the Scout dossier rather than re-interpreting the whole source.
- Reviewer: compare source wording to tests/code and report only source-fidelity, missing-test, or maintainability findings.

Each council dossier should capture:

| Field | Notes |
| --- | --- |
| Source | Official council PDF/webpage or legislation, scheme year, retrieved date, paragraph/page refs. |
| Archetype | Legacy means test, percent/minimum-payment, income banded, UC earnings banded, band cap, or custom. |
| Core rules | Maximum support, taper, capital limit, band cap, UC treatment, non-dependant table, pensioner carve-out. |
| Tests | No-income maximum award, capital cutoff, non-dep case, UC case if relevant, and one local edge. |
| Review traps | Weekly vs annual units, gross vs earned income, positive earnings vs remunerative work, UC couple exceptions. |

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
| Oxford | Implemented | Weekly income-banded support with local non-dependant table | https://www.oxford.gov.uk/council-tax-reduction/council-tax-reduction-scheme-2026-27 |
| Kingston upon Thames | Implemented | Legacy full support with 2026/27 remunerative-work non-dependant deductions | https://www.kingston.gov.uk/sites/default/files/2026-03/Council%20Tax%20Reduction%20Scheme%202026%20-%202027.pdf |
| Newham | Implemented | Legacy 70 percent with `25%` taper, `GBP 6,000` capital limit, and local non-dependant deductions | https://www.newham.gov.uk/downloads/file/10753/council-tax-reduction-scheme-2026 |
| Westminster | Implemented | Legacy full support with 2026/27 remunerative-work non-dependant deductions | https://www.westminster.gov.uk/sites/default/files/media/documents/council-tax-support-scheme-for-2026-27.pdf |
| Greenwich | Implemented | Legacy 80 percent with `25%` taper, tariff income, and flat working-age non-dependant deduction | https://www.royalgreenwich.gov.uk/help-money/get-help-paying-your-housing-costs-and-council-tax/apply-help-pay-your-council-tax/how-much |
| Hackney | Implemented | Legacy 90 percent with tariff income and 2026/27 remunerative-work non-dependant deductions | https://www.hackney.gov.uk/council-tax-and-benefits/benefits/benefits-explained/housing-benefit-and-council-tax-reduction-explained |
| Hammersmith and Fulham | Implemented | Legacy full support with tariff income and 2026/27 uprated non-dependant deductions | https://democracy.lbhf.gov.uk/documents/s133438/Council%20Tax%20Support%20Scheme%202026-27.pdf |
| Stockport | Implemented | Legacy full support with Band A/B caps, tariff income, and two-rate gross-income non-dependant deductions | https://www.stockport.gov.uk/council-tax-support-scheme |
| Wakefield | Implemented | Working-age non-DWP income bands with flat non-dependant deductions | https://www.wakefield.gov.uk/council-tax/help-with-your-council-tax/working-age-council-tax-support-scheme |
| Tameside | Implemented | Weekly net-income bands with Band A cap and no non-dependant deductions | https://tameside.moderngov.co.uk/documents/s200335/Appendix.%202%20for%20Council%20Tax%20Support%20Scheme%202026-2027.pdf |
| Bury | Implemented | Monthly earnings-banded discount with Band B cap and flat non-dependant deductions | https://www.bury.gov.uk/asset-library/bury-cts-scheme-policy-2026-27.pdf |
| Lambeth | Implemented | Weekly net-earnings bands with working-age savings limit and working/non-working non-dependant deductions | https://www.lambeth.gov.uk/about-housing-benefit-council-tax-support/council-tax-support/how-much-council-tax-support-you-can-get |
| Camden | Implemented | Weekly gross-earnings bands after eligible childcare costs, with protected group table and liability-share non-dependant deductions | https://www.camden.gov.uk/council-tax-support |
| Islington | Implemented | Weekly net-earnings bands with protected zero-earnings rules and flat non-dependant deductions | https://www.islington.gov.uk/benefits-and-support/council-tax-support |
| Barking and Dagenham | Implemented | Weekly net-income bands by household type with `GBP 6,000` capital limit and pre-percentage flat non-dependant deductions | https://lbbd.moderngov.co.uk/documents/s178487/CTSS%202026-27%20-%20App%202.pdf |
| Barnet | Implemented | Monthly earnings-banded discount with Band C cap, `GBP 6,000` capital limit, and two-rate non-dependant deductions | https://barnet.moderngov.co.uk/documents/s94210/Appendix%20O%20-%20202627%20Council%20Tax%20Support%20Scheme.pdf |
| Ealing | Implemented | Weekly income-banded support with protected and non-protected tables, strict `GBP 6,000` capital cutoff, and local non-dependant deductions | https://www.ealing.gov.uk/download/downloads/id/19657/council_tax_reduction_scheme_2026_to_2027.pdf |
| Enfield | Implemented | Non-UC legacy means test with `50%` cap, Band C liability cap and `22.5%` taper, plus UC net-earnings bands and protected groups | https://www.enfield.gov.uk/__data/assets/pdf_file/0019/126262/Council-tax-reduction-scheme-2026-to-2027-Benefits-and-money-advice.pdf |
| Hillingdon | Implemented | Weekly net-income bands with vulnerable Band 2, Band D cap for Bands 3-6, `GBP 6,000` capital limit, and flat non-dependant deductions | https://pre.hillingdon.gov.uk/benefits/working-age-bands |

## Reviewed Candidate Queue

| Authority | Status | Type | Notes |
| --- | --- | --- | --- |
