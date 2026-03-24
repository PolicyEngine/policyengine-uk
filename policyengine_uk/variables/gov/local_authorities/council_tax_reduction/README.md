# Council Tax Reduction

This implementation currently simulates:

- The statutory CTR scheme for pensioner households in England.
- The national CTR scheme in Wales.
- The national CTR scheme in Scotland.
- Working-age local schemes for Chesterfield, Dudley, East Hertfordshire, Stevenage, Stroud, and Warrington.

For unsupported English working-age authorities, the model continues to use reported `council_tax_benefit` values in dataset mode rather than inventing scheme rules.

The current implementation does not yet model:

- Authority-specific income-banded English schemes.
- Alternative maximum / second adult rebate cases.
- Universal Credit-specific CTR adjustments beyond the standard income treatment used here.

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
- Stevenage (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's published scheme says working-age claimants receive `91.5%` of net liability, so PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`.
- Chesterfield (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's published scheme says working-age claimants receive `91.5%` of net liability, so PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`.
- Warrington (`WA1 1UH`, band `C`, single working-age owner-occupier, no children, no savings, income-based JSA): entitledto returns `GBP 26.69` per week of Council Tax Support and `GBP 2.48` per week left to pay on a displayed bill of `GBP 29.17` per week, which is a `91.5%` maximum award on the displayed weekly bill. PolicyEngine UK applies the same rule structure.
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
