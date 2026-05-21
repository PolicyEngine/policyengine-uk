# Council Tax and CTR Pipeline

This branch is a contingent scaffold for work that should merge after
UK-wide Council Tax Reduction (CTR) support lands in
PolicyEngine/policyengine-uk#1534.

## Current semantics

- `council_tax` is the household dataset's gross annual Council Tax
  liability. It is an input, not yet recomputed from local authority
  schedules.
- `council_tax_reduction` is currently hybrid: it uses modelled CTR for
  supported local schemes and reported CTB/CTR for unsupported schemes.
- `council_tax_less_benefit` is gross Council Tax minus that hybrid
  reduction amount, floored at zero. It is the right household signal for
  net Council Tax receipts targets during the transition.

## Dependency boundary

Until #1534 is complete, downstream pipeline changes should stay
compare-only. They may add variables, targets, diagnostics, or tests, but
should not switch household net income or calibration production outputs
from FRS-reported or hybrid Council Tax/CTB onto fully modelled CTR.

## Draft PR sequence

1. Clarify variable semantics and add tests for the gross-to-net Council
   Tax calculation. This PR is that first step.
2. Add structural gross Council Tax variables from local authority, band,
   ratios, discounts, and rates. Keep them compare-only against the
   current `council_tax` input.
3. Add CTR calibration diagnostics in `policyengine-uk-data`, comparing
   modelled CTR and `council_tax_less_benefit` against admin spend,
   caseload, and net receipts targets where available.
4. Switch the production dataset pipeline to structural gross Council Tax
   minus modelled CTR only after UK-wide CTR schemes are implemented and
   diagnostics show the switch is acceptable.
