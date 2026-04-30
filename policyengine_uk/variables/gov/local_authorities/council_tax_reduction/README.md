# Council Tax Reduction

This implementation currently simulates:

- The statutory CTR scheme for pensioner households in England.
- The national CTR scheme in Wales.
- The national CTR scheme in Scotland.
- Working-age local schemes for Adur, Basingstoke and Deane, Bolton, Breckland, Broadland, Chesterfield, Crawley, Darlington, Dudley, East Cambridgeshire, East Hertfordshire, East Suffolk, Fenland, Gateshead, King's Lynn and West Norfolk, Lancaster, Merton, North Norfolk, Norwich, Oldham, South Norfolk, Southwark, St Albans, Stevenage, Stroud, Warrington, West Suffolk, and Worthing.

For unsupported English working-age authorities, the model continues to use reported `council_tax_benefit` values in dataset mode rather than inventing scheme rules.

The top-level `simulated_council_tax_reduction_benunit` variable aggregates implemented jurisdiction-specific CTR variables. Working-age local authority rules live under `policyengine_uk/variables/gov/local_authorities/<authority>/council_tax_reduction/`, matching the parameter tree and keeping each council's policy in its own jurisdiction folder.

The current implementation does not yet model:

- Authority-specific income-banded English schemes, except the St Albans Universal Credit earnings-band path.
- Alternative maximum / second adult rebate cases.
- Universal Credit-specific CTR adjustments beyond the St Albans earnings-band path and standard income treatment used here.
- National/statutory non-dependant couple aggregation beyond the local working-age scheme helper.
- Non-dependant deduction apportionment across multiple jointly liable Council Tax payers.

For batched implementation status and next candidates, see `scheme_work_queue.md`.

There is also a requests-based entitledto comparison harness at `scripts/entitledto_ctr_compare.py`. It replays the calculator from a saved browser storage state and currently covers three single-adult claimant variants:

- `single_jsa`
- `single_jsa_pip_standard`
- `single_pension_credit`

It does not yet cover couples, children, or other-adult/non-dependant household shapes. entitledto's session handling is also inconsistent enough that rerunning with a fresh storage state is sometimes necessary, and fresh anonymous calculator starts can hit entitledto's day limit. A typical single-scenario run is:

`uv run --with requests --with beautifulsoup4 python scripts/entitledto_ctr_compare.py output/playwright/entitledto-live-state.json --postcode SG13 8EQ --band D --council-tax 1800 --scenario single_jsa`

There is also a requests-based Turn2us probe at `scripts/turn2us_ctr_compare.py`. It currently replays the public Turn2us calculator for a single working-age JSA claimant and records the benefits that appear on the final results page for the supplied postcode. A typical multi-authority run is:

`uv run --with requests python scripts/turn2us_ctr_compare.py "SG13 8EQ" "WA1 1UH" "DY1 1HF" "GL5 4UB"`

## Validation notes

Spot checks against public calculators and scheme sources currently show:

- Stroud (`GL5 4UB`, area `Stroud`, band `D`, single working-age owner-occupier, no children, no savings, income-based JSA): entitledto returns full Council Tax Support on an annual liability of `GBP 1,866.47`. PolicyEngine UK returns `council_tax_reduction = GBP 1,866.47`.
- Dudley (`DY1 1HF`, band `C`, single working-age owner-occupier, no children, no savings, income-based JSA): entitledto returns `GBP 15.64` per week of Council Tax Support, leaving `GBP 10.43` per week to pay. PolicyEngine UK returns `council_tax_reduction = GBP 543.62` per year and `council_tax_less_benefit = GBP 815.43` per year, matching Dudley Council's published 2025/26 scheme text and scheme PDF rather than the entitledto output.
- East Hertfordshire (`SG13 8EQ`, band `D`, single working-age owner-occupier, no children, no savings, income-based JSA, annual liability `GBP 1,800`): entitledto returns `GBP 31.59` per week of Council Tax Support and `GBP 2.93` per week left to pay. PolicyEngine UK applies the same `91.5%` maximum award rule, giving `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153` per year.
- East Hertfordshire (`SG13 8EQ`, band `D`, single working-age lone parent, one child aged `5`, no savings, income-based JSA, annual liability `GBP 1,800`): a headed browser run through entitledto returns total benefits of `GBP 367.64` per week, made up of `GBP 310.00` income-based Jobseeker's Allowance, `GBP 31.59` Council Tax Support, and `GBP 26.05` Child Benefit. The calculator shows a weekly Council Tax bill of `GBP 34.52` reduced to `GBP 2.93`. PolicyEngine UK now keeps this household on the East Herts class D maximum award, returning `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`.
- East Hertfordshire (`SG13 8EQ`, band `D`, two working-age adults, no children, no savings, income-based JSA, annual liability `GBP 1,800`): a headed browser run through entitledto returns total benefits of `GBP 237.89` per week, made up of `GBP 206.30` income-based Jobseeker's Allowance and `GBP 31.59` Council Tax Support. The calculator again shows a weekly Council Tax bill of `GBP 34.52` reduced to `GBP 2.93`. PolicyEngine UK returns the same annual CTR position, `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`. Because this check reused an existing entitledto calculation ID to get around the anonymous daily cap, the Council Tax page initially carried forward a stale `25%` single-adult discount and had to be corrected back to `none` before the result was trusted.
- East Cambridgeshire (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `91.5%` of eligible Council Tax after discounts and non-dependant deductions, with the standard `2 6/7%` daily excess-income percentage and the ARP flat working-age non-dependant deduction. PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153` before non-dependant deductions.
- East Suffolk (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `91.5%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage, equivalent to a `20%` weekly taper. Anglia Revenues Partnership says working-age CTR applicants need less than `GBP 10,000` in capital and publishes a flat `GBP 8.34` working-age non-dependant deduction for 2026/27. PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153` before non-dependant deductions.
- Breckland (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `91.5%` of eligible Council Tax after discounts and non-dependant deductions, with the standard `2 6/7%` daily excess-income percentage and the ARP flat working-age non-dependant deduction. PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153` before non-dependant deductions.
- Fenland (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the standard `2 6/7%` daily excess-income percentage and the ARP flat working-age non-dependant deduction. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions.
- West Suffolk (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `100%` for the period from `1 April 2023` through `31 March 2026`, then `91.5%` after `31 March 2026`, with the standard `2 6/7%` daily excess-income percentage and the ARP flat working-age non-dependant deduction. PolicyEngine UK returns `GBP 1,800` in 2025 and `GBP 1,647` in 2026 before non-dependant deductions.
- Broadland (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says working-age applicants who are not receiving a war pension can receive up to `87%` of eligible Council Tax, with a `20%` taper, a `GBP 16,000` capital limit, and a flat `GBP 7` weekly working-age non-dependant deduction. The council's 2026/27 papers say the existing scheme continues with no changes. PolicyEngine UK returns `council_tax_reduction = GBP 1,566` and `council_tax_less_benefit = GBP 234` before non-dependant deductions.
- South Norfolk (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says working-age applicants who are not receiving a war pension can receive up to `87%` of eligible Council Tax, with a `20%` taper, a `GBP 16,000` capital limit, and a flat `GBP 7` weekly working-age non-dependant deduction. The council's 2026/27 papers say the existing scheme continues with no changes. PolicyEngine UK returns `council_tax_reduction = GBP 1,566` and `council_tax_less_benefit = GBP 234` before non-dependant deductions.
- Lancaster (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage, equivalent to a `20%` weekly taper, and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions.
- Oldham (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme caps working-age eligible liability at Band A and applies a `15%` reduction in award, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,020` and `council_tax_less_benefit = GBP 780` before non-dependant deductions.
- Bolton (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme says maximum Council Tax Support is `82.5%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,485` and `council_tax_less_benefit = GBP 315` before non-dependant deductions.
- Basingstoke and Deane (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme says maximum Council Tax Support is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions.
- Crawley (working-age, band `D`, annual liability `GBP 1,800`, no children, savings below `GBP 9,000`): the council's 2025/26 scheme says maximum Council Tax Reduction is `100%` of eligible Council Tax after discounts and non-dependant deductions, with a `GBP 9,000` capital limit and a `20%` weekly taper. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions, and returns no support above the capital limit.
- St Albans (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says non-Universal Credit claimants can receive `100%` of eligible Council Tax with the standard `20%` weekly taper and a `GBP 16,000` capital limit. For Universal Credit claimants, St Albans uses an earnings-band contribution table. PolicyEngine UK returns `GBP 1,800` for the non-UC no-income case, and `GBP 660` where monthly earnings of `GBP 1,000` imply a `GBP 95` monthly contribution in 2025. The scheme excludes Universal Credit awards from its one-deduction non-dependant couple rule; PolicyEngine UK counts both members in that case.
- Adur (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme says maximum Council Tax Support is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions. The scheme excludes Universal Credit awards from its one-deduction non-dependant couple rule; PolicyEngine UK counts both members in that case.
- Worthing (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2026/27 scheme says maximum Council Tax Support is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit. PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0` before non-dependant deductions. The scheme excludes Universal Credit awards from its one-deduction non-dependant couple rule; PolicyEngine UK counts both members in that case.
- Stevenage (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's published scheme says working-age claimants receive `91.5%` of net liability, so PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`.
- Chesterfield (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's published scheme says working-age claimants receive `91.5%` of net liability, so PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`.
- Warrington (`WA1 1UH`, band `C`, single working-age owner-occupier, no children, no savings, income-based JSA): entitledto returns `GBP 26.69` per week of Council Tax Support and `GBP 2.48` per week left to pay on a displayed bill of `GBP 29.17` per week, which is a `91.5%` maximum award on the displayed weekly bill. PolicyEngine UK applies the same rule structure.
- Merton (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's published calculation guide says maximum Council Tax Support is usually `100%` of eligible Council Tax after discounts and non-dependant deductions, with a `20%` taper and a `GBP 16,000` capital limit, so PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0`.
- Southwark (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's published 2025/26 policy summary says working-age applicants can receive up to `85%` of annual council tax liability, with a `20%` taper and a `GBP 16,000` capital limit, so PolicyEngine UK returns `council_tax_reduction = GBP 1,530` and `council_tax_less_benefit = GBP 270`.
- Darlington (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says working-age support is up to `80%` of eligible Council Tax, with a `20%` taper and a `GBP 16,000` capital limit, so PolicyEngine UK returns `council_tax_reduction = GBP 1,440` and `council_tax_less_benefit = GBP 360`.
- Gateshead (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says working-age households can receive support up to `91.5%` of their council tax bill and uses the `2 6/7%` daily excess-income percentage, equivalent to a `20%` weekly taper, so PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`. The same source also sets a Gateshead-specific 2025/26 non-dependant deduction schedule, which PolicyEngine UK applies instead of the Housing Benefit schedule.
- King's Lynn and West Norfolk (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 and 2026/27 scheme regulations say maximum Council Tax Reduction is `100%` of eligible Council Tax after discounts and non-dependant deductions, with a `2 6/7%` daily excess-income percentage, equivalent to a `20%` weekly taper, and a `GBP 16,000` capital limit, so PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0`. The scheme text says non-dependant deductions are uprated by the prescribed requirements regulations, so PolicyEngine UK uses the council's current non-dependant table for the applied 2025 and 2026 values.
- Norwich (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 and 2026 scheme PDFs say maximum Council Tax Reduction is `100%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage and a `GBP 16,000` capital limit, so PolicyEngine UK returns `council_tax_reduction = GBP 1,800` and `council_tax_less_benefit = GBP 0`. Norwich sets a separate working-age non-dependant deduction schedule, which PolicyEngine UK applies instead of the Housing Benefit schedule.
- North Norfolk (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's 2025/26 scheme says maximum Council Tax Reduction is `91.5%` of eligible Council Tax after discounts and non-dependant deductions, with the `2 6/7%` daily excess-income percentage, equivalent to a `20%` weekly taper, and a `GBP 16,000` capital limit. The council's April 2026 update says the 2026/27 scheme continues under the arrangements introduced from `1 April 2025`. PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`. The same source sets a flat `GBP 10` weekly non-dependant deduction and waives it where the claimant or partner receives the Limited Capability for Work component of Universal Credit.
- Policy in Practice Better Off Calculator (`SG13 8EQ`, East Hertfordshire, band `D`, single working-age owner-occupier, no children, no savings, income-based JSA, monthly council tax liability `GBP 150`): the public calculator resolves East Hertfordshire from postcode and returns `GBP 137.25` per month of Council Tax Support. That is exactly a `91.5%` award on the entered liability, matching the scheme structure and the PolicyEngine UK rule.
- Policy in Practice Better Off Calculator (`DY1 1HF`, Dudley, band `C`, single working-age owner-occupier, no children, no savings, income-based JSA, monthly council tax liability `GBP 113.25` with single-person discount): the public calculator resolves Dudley from postcode and returns `GBP 45.30` per month of Council Tax Support. That is exactly a `40%` award on the entered liability, matching Dudley's published scheme structure and the PolicyEngine UK rule.
- Policy in Practice Better Off Calculator (`WA1 1UH`, Warrington, band `C`, single working-age owner-occupier, no children, no savings, income-based JSA, monthly council tax liability `GBP 126.74` with single-person discount): the public calculator resolves Warrington from postcode and returns `GBP 95.06` per month of Council Tax Support. That is a `75%` award on the entered liability, which does not match Warrington's published 2025/26 Class D passported-JSA scheme, entitledto's `91.5%` result for the same scenario, or the current PolicyEngine UK encoding.
- Policy in Practice Better Off Calculator (`GL5 4UB`, Stroud, band `D`, single working-age owner-occupier, no children, no savings, income-based JSA, monthly council tax liability `GBP 148.09` with single-person discount): the public calculator resolves Stroud from postcode and returns `GBP 148.09` per month of Council Tax Support. That is full support on the entered liability, matching entitledto's behavior and the published Stroud scheme summary.
- Turn2us public calculator checks on the same four single working-age owner-occupier income-based JSA cases in East Hertfordshire, Warrington, Dudley, and Stroud all reached the final results page, but returned the same `Income-based Jobseekers Allowance` and `Universal Credit` lines for all four authorities and no CTR output. In these cases, Turn2us was not acting as an authority-specific CTR comparator.

For the East Hertfordshire and Warrington calculator checks, entitledto's annual tab appears to multiply rounded weekly outputs by `52`, so the weekly figures are the closest comparison point. Additional browser-only probing suggests that reusing an existing entitledto calculation ID is good enough for lone-parent and couple spot checks, but not yet good enough for other-adult/non-dependant cases: the later pages can retain stale branch state, so those results should not be treated as validated until the flow is replayed from a fresh entitledto session.

The public Policy in Practice calculator is testable through the browser, but not through a simple documented one-shot API. The frontend is a token-gated SPA on `betteroffcalculator.co.uk` backed by `api.betteroffcalculator.co.uk`; raw ad hoc `POST /api` requests return default baseline results unless the full calculator state has already been established in the session.

Dudley references:

- https://www.dudley.gov.uk/residents/benefits/council-tax-reduction-scheme/
- https://www.dudley.gov.uk/media/khllf4zc/dudley-council-tax-reduction-scheme-2025-26.pdf

East Hertfordshire references:

- https://www.eastherts.gov.uk/benefits-and-financial-support/council-tax-support
- https://cdn-eastherts.onwebcurl.com/s3fs-public/2025-03/East%20Herts%20S13a%20202526%20Scheme%20Final.pdf

East Suffolk references:

- https://www.angliarevenues.gov.uk/services/counciltax/reductions/what-is-ctax-reduction/upload/East-Suffolk-Council-Council-Tax-Reduction-Scheme-2025-26.pdf
- https://www.angliarevenues.gov.uk/services/housing-benefits/apply/
- https://www.angliarevenues.gov.uk/services/housing-benefits/non-dependant-deductions-ctrs.cfm

East Cambridgeshire references:

- https://www.angliarevenues.gov.uk/services/counciltax/reductions/what-is-ctax-reduction/upload/East-Cambridgeshire-District-Council-Council-Tax-Reduction-Schemes-2025-26.pdf
- https://www.angliarevenues.gov.uk/services/housing-benefits/apply/
- https://www.angliarevenues.gov.uk/services/housing-benefits/non-dependant-deductions-ctrs.cfm

Breckland references:

- https://www.angliarevenues.gov.uk/services/counciltax/reductions/what-is-ctax-reduction/upload/Breckland-Council-Tax-Reduction-Scheme-2025-26.pdf
- https://www.angliarevenues.gov.uk/services/housing-benefits/apply/
- https://www.angliarevenues.gov.uk/services/housing-benefits/non-dependant-deductions-ctrs.cfm

Broadland references:

- https://www.southnorfolkandbroadland.gov.uk/asset-library/broadland-ctr-scheme-2025-26.pdf
- https://southnorfolkandbroadland.moderngov.co.uk/documents/s12491/CTAX%20Reduction%20Scheme.pdf

Fenland references:

- https://www.angliarevenues.gov.uk/services/counciltax/reductions/what-is-ctax-reduction/upload/Fenland-District-Council-Council-Tax-Reduction-Scheme-2025-26.pdf
- https://www.angliarevenues.gov.uk/services/housing-benefits/apply/
- https://www.angliarevenues.gov.uk/services/housing-benefits/non-dependant-deductions-ctrs.cfm

West Suffolk references:

- https://www.angliarevenues.gov.uk/services/counciltax/reductions/what-is-ctax-reduction/upload/West-Suffolk-Council-Council-Tax-Reduction-Scheme-2025-26.pdf
- https://www.angliarevenues.gov.uk/services/housing-benefits/apply/
- https://www.angliarevenues.gov.uk/services/housing-benefits/non-dependant-deductions-ctrs.cfm

South Norfolk references:

- https://www.southnorfolkandbroadland.gov.uk/asset-library/south-norfolk-ctr-scheme-2025-26.pdf
- https://southnorfolkandbroadland.moderngov.co.uk/documents/g1058/Printed%20minutes%2024th-Nov-2025%2009.00%20South%20Norfolk%20Cabinet.pdf?T=1

Lancaster references:

- https://www.lancaster.gov.uk/assets/attach/14831/lancaster-city-council-2025-26-council-tax-support-scheme.pdf

Oldham references:

- https://www.oldham.gov.uk/download/downloads/id/2632/council_tax_reduction_scheme_2025-26.pdf

Bolton references:

- https://www.bolton.gov.uk/downloads/file/745/bolton-council-tax-reduction-scheme

Basingstoke and Deane references:

- https://www.basingstoke.gov.uk/content/page/77332/Basingstoke%20S13A%202026%20Scheme%20Final.pdf

Crawley references:

- https://crawley.gov.uk/sites/default/files/2025-02/Council%20Tax%20Reduction%20scheme%202025%20to%202026.pdf

St Albans references:

- https://www.stalbans.gov.uk/sites/default/files/attachments/St%20Albans%20S13A%20202526%20Final.pdf
- https://www.stalbans.gov.uk/council-tax-support

Adur references:

- https://www.adur-worthing.gov.uk/media/Media,174007,smxx.pdf
- https://www.adur-worthing.gov.uk/benefits/council-tax-support/

Worthing references:

- https://www.adur-worthing.gov.uk/media/Media,174008,smxx.pdf
- https://www.adur-worthing.gov.uk/benefits/council-tax-support/

Stevenage references:

- https://www.stevenage.gov.uk/benefits/council-tax-support
- https://www.stevenage.gov.uk/documents/council-tax/council-tax-support-scheme-2025-26.pdf

Chesterfield references:

- https://www.chesterfield.gov.uk/council-tax-and-business-rates/council-tax/council-tax-support
- https://www.chesterfield.gov.uk/media/zuxllbgk/chesterfield-borough-council-council-tax-support-scheme-2019-20.pdf

Warrington references:

- https://www.warrington.gov.uk/benefits-calculator
- https://www.warrington.gov.uk/income-and-capital
- https://www.warrington.gov.uk/non-dependants
- https://www.warrington.gov.uk/sites/default/files/2025-04/CTS%20Scheme%202025-26.pdf

Merton references:

- https://www.merton.gov.uk/sites/default/files/2025-03/Council%20Tax%20Reduction%20Scheme%20L%20B%20Merton%202025-26.pdf
- https://www.merton.gov.uk/council-tax-benefits-and-housing/benefits/council-tax-support/calculating-council-tax-support
- https://www.merton.gov.uk/council-tax-benefits-and-housing/benefits/council-tax-support/council-tax-support-scheme-consultations-and-official-text

Southwark references:

- https://www.southwark.gov.uk/council-tax/get-money-your-council-tax-bill/council-tax-reduction/how-much-your-bill-can-be-reduced
- https://www.southwark.gov.uk/sites/default/files/2025-03/Southwark%20Council%20Tax%20Reduction%20Policy%202025-26.pdf
- https://www.southwark.gov.uk/sites/default/files/2025-03/Southwark%20Council%20Tax%20Reducation%20Policy%202025-26%20shorter%20version.pdf

Darlington references:

- https://www.darlington.gov.uk/media/czqfj5rz/council-tax-support-scheme-25-26-final.pdf

Gateshead references:

- https://www.gateshead.gov.uk/article/27558/Part-1-Introduction
- https://www.gateshead.gov.uk/article/27575/Part-4-Classes-of-person-entitled-to-a-reduction-under-this-scheme
- https://www.gateshead.gov.uk/article/27582/Part-7-Maximum-council-tax-reduction-for-the-purposes-of-calculating-eligibility-for-a-reduction-under-this-scheme-and-the-amount-of-reduction
- https://www.gateshead.gov.uk/article/27578/Part-5-Classes-of-person-excluded-from-this-scheme

King's Lynn and West Norfolk references:

- https://www.west-norfolk.gov.uk/download/downloads/id/9853/council_tax_reduction_scheme_2025_to_2026.pdf
- https://www.west-norfolk.gov.uk/download/downloads/id/3330/council_tax_support_regulations.pdf
- https://www.west-norfolk.gov.uk/info/20019/council_tax_support/29/council_tax_support_-_non-dependants

Norwich references:

- https://www.norwich.gov.uk/download/downloads/id/10735/council_tax_reduction_scheme_2025-26.pdf
- https://www.norwich.gov.uk/sites/default/files/2026-03/Council-Tax-Reduction-Scheme-2026.pdf

North Norfolk references:

- https://www.north-norfolk.gov.uk/media/10894/north-norfolk-council-tax-reduction-scheme-for-2025-to-2026.pdf
- https://www.north-norfolk.gov.uk/tasks/benefits/housing-benefit-and-council-tax-support-rates-from-april-2026/
