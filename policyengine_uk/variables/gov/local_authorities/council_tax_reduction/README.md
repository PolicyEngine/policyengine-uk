# Council Tax Reduction

This implementation currently simulates:

- The statutory CTR scheme for pensioner households in England.
- The national CTR scheme in Wales.
- The national CTR scheme in Scotland.
- Working-age local schemes for East Hertfordshire, Stroud, Warrington, and Dudley.

For unsupported English working-age authorities, the model continues to use reported `council_tax_benefit` values in dataset mode rather than inventing scheme rules.

The current implementation does not yet model:

- Authority-specific income-banded English schemes.
- Alternative maximum / second adult rebate cases.
- Universal Credit-specific CTR adjustments beyond the standard income treatment used here.

## Validation notes

Spot checks against public calculators and scheme sources currently show:

- Stroud (`GL5 4UB`, area `Stroud`, band `D`, single working-age owner-occupier, no children, no savings, income-based JSA): entitledto returns full Council Tax Support on an annual liability of `GBP 1,866.47`. PolicyEngine UK returns `council_tax_reduction = GBP 1,866.47`.
- Dudley (`DY1 1HF`, band `C`, single working-age owner-occupier, no children, no savings, income-based JSA): entitledto returns `GBP 15.64` per week of Council Tax Support, leaving `GBP 10.43` per week to pay. PolicyEngine UK returns `council_tax_reduction = GBP 543.62` per year and `council_tax_less_benefit = GBP 815.43` per year, matching Dudley Council's published 2025/26 scheme text and scheme PDF rather than the entitledto output.
- East Hertfordshire (working-age, band `D`, annual liability `GBP 1,800`, no children, no savings): the council's published scheme says working-age claimants receive `91.5%` of net liability, so PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`.
- Warrington (working-age, band `C`, annual liability `GBP 1,800`, no children, no savings, income-based JSA-style low-income case): Warrington's public guidance says Band `B` and above receive `91.5%` of liability at the maximum award, so PolicyEngine UK returns `council_tax_reduction = GBP 1,647` and `council_tax_less_benefit = GBP 153`.

Automated entitledto checks for the East Hertfordshire and Warrington additions were attempted on March 23, 2026, but entitledto's public calculator returned its Cloudflare challenge and then the site's generic error page in browser automation. The two new notes above therefore rely on the councils' published scheme materials rather than calculator output.

Dudley references:

- https://www.dudley.gov.uk/residents/benefits/council-tax-reduction-scheme/
- https://www.dudley.gov.uk/media/khllf4zc/dudley-council-tax-reduction-scheme-2025-26.pdf

East Hertfordshire references:

- https://www.eastherts.gov.uk/benefits-and-financial-support/council-tax-support
- https://cdn-eastherts.onwebcurl.com/s3fs-public/2025-03/East%20Herts%20S13a%20202526%20Scheme%20Final.pdf

Warrington references:

- https://www.warrington.gov.uk/benefits-calculator
- https://www.warrington.gov.uk/income-and-capital
- https://www.warrington.gov.uk/non-dependants
- https://www.warrington.gov.uk/sites/default/files/2025-04/CTS%20Scheme%202025-26.pdf
