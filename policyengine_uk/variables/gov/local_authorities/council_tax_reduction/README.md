# Council Tax Reduction

This implementation currently simulates:

- The national-style legacy/default CTR calculation for households in Wales, Scotland, and English pension-age cases.
- Explicit working-age overrides for Stroud and Dudley.

For unsupported English working-age authorities, the model continues to use reported `council_tax_benefit` values in dataset mode rather than inventing scheme rules.

The current implementation does not yet model:

- Authority-specific income-banded English schemes.
- Alternative maximum / second adult rebate cases.
- Universal Credit-specific CTR adjustments beyond the standard income treatment used here.

## Validation notes

Spot checks against entitledto's public calculator currently show:

- Stroud (`GL5 4UB`, area `Stroud`, band `D`, single working-age owner-occupier, no children, no savings, income-based JSA): entitledto returns full Council Tax Support on an annual liability of `GBP 1,866.47`. PolicyEngine UK returns `council_tax_reduction = GBP 1,866.47`.
- Dudley (`DY1 1HF`, band `C`, single working-age owner-occupier, no children, no savings, income-based JSA): entitledto returns `GBP 15.64` per week of Council Tax Support, leaving `GBP 10.43` per week to pay. PolicyEngine UK returns `council_tax_reduction = GBP 543.62` per year and `council_tax_less_benefit = GBP 815.43` per year, matching Dudley Council's published 2025/26 scheme text and scheme PDF rather than the entitledto output.

Dudley references:

- https://www.dudley.gov.uk/residents/benefits/council-tax-reduction-scheme/
- https://www.dudley.gov.uk/media/khllf4zc/dudley-council-tax-reduction-scheme-2025-26.pdf
