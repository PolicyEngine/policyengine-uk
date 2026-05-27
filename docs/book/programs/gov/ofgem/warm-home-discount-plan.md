# Warm Home Discount (planned)

```{warning}
**Not yet modelled.** The Warm Home Discount (WHD) is an Ofgem-administered
scheme that pays a one-off rebate of £150 per qualifying household per
winter, off their domestic electricity bill. PolicyEngine UK doesn't
currently model it. This page captures the proposed scope, tracked
under [#502](https://github.com/PolicyEngine/policyengine-uk/issues/502).
```

## Why modelling WHD is harder than it looks

The Warm Home Discount has two components, with different eligibility
rules:

- **Core Group 1**: people in receipt of the **Guarantee Credit element
  of Pension Credit**. This group is identified automatically by DWP
  data-matching and the rebate is applied to their electricity bill
  without an application. Eligibility for this group is a clean,
  centrally-defined rule and is straightforwardly modellable from the
  existing PolicyEngine variables (`pension_credit`).
- **Core Group 2** ("Broader Group" until 2022-23): people whose home is
  **assessed as having a high energy cost** and who are on certain
  qualifying means-tested benefits (UC, IS, JSA-IB, ESA-IR, HB, CTC, WTC
  in particular bands). The high-energy-cost assessment uses an
  Energy Performance Certificate (EPC) plus VOA property data; the
  qualifying-benefit list shifted in England in 2022-23 ([source][gov-2022]).

The combination of (a) the EPC-based property assessment, (b) different
schemes in England, Scotland, and Wales, and (c) the absence of a
public point-in-time eligibility register makes this harder to model
than typical means-tested benefits.

## Devolved variants

| Nation | Core 1 (PC Guarantee Credit) | Core 2 ("Broader Group") |
|--------|-------------------------------|---------------------------|
| England | yes — auto, £150 | yes — EPC-based property assessment + qualifying benefits |
| Scotland | yes — auto, £150 | by **application** through energy suppliers; criteria vary year to year |
| Wales | yes — auto, £150 | by **application** through energy suppliers; criteria vary year to year |

Scotland and Wales did not adopt the 2022 England reform that swapped
the application-based Broader Group for the EPC-based Core 2; instead
both retain the application model.

## Proposed scope

### Phase 1 — Core Group 1 only

The single cleanest WHD modelling target: payment to any household
with positive `pension_credit_guarantee_credit` in the winter season.
~1 million households per year by DWP outturn (out of ~3 million WHD
recipients).

- New parameter `gov.ofgem.warm_home_discount.core_group_1.amount`
  (£150 since winter 2022-23, £140 before).
- New variable `warm_home_discount_core_1` (Household, YEAR) =
  `amount` if any benunit member has positive Pension Credit Guarantee
  Credit, else 0.
- Roll into a `warm_home_discount` umbrella variable; Phase 2 adds the
  Core Group 2 leg.

### Phase 2 — Core Group 2 (England)

Requires:

- Adding EPC band as a household input variable (or imputing it from
  property age/type via a `policyengine-uk-data` second-stage QRF).
- Encoding the qualifying-benefit list per scheme year (the list
  changed in winter 2022-23).
- Property-cost-score parameters from Ofgem's annual scheme rules.

This is the bulk of the work.

### Phase 3 — Scotland and Wales

Application-based Core 2 isn't modellable from administrative
eligibility rules alone. The reasonable approximation is a take-up rate
applied to the same qualifying-benefit set:

- A `would_claim_warm_home_discount_scotland` / `_wales` stochastic
  flag in `policyengine-uk-data` calibrated against Ofgem-published
  Scottish/Welsh recipient counts.

## Alternative: model as a Core 1-only umbrella

Given the complexity of Phase 2 and the relatively modest fiscal
weight of WHD (~£400m/year on Core 1 across the UK), a defensible v1
is to model **only** Core Group 1 and document Core Group 2 as
under-imputed. That captures the most policy-relevant slice (Pension
Credit interaction, eligibility through the means-tested-benefit
ladder) at minimal modelling cost.

Reform analysis using PolicyEngine to "expand WHD to all UC
households" or similar would still work with Phase 1 alone by setting
a Core-1-equivalent uplift on the WHD parameter.

## Data needs

- **Ofgem WHD statistics**:
  [Warm Home Discount Scheme: annual reports](https://www.ofgem.gov.uk/publications/warm-home-discount-annual-reports)
  give per-scheme-year recipient counts and total spend by group.
- **DWP Pension Credit caseload** — already used for Pension Credit
  calibration; no new data work needed for Phase 1.
- **EPC distribution by property type** for Phase 2 — VOA + ONS data
  exist but need cross-walking to FRS rows.

## Open questions

- The WHD scheme year runs October to March; PolicyEngine UK
  variables are year-level. Should the variable represent the rebate
  paid during the simulation year (Oct-Mar payments), or the rebate
  accrued during the simulation year (Mar-Oct accrual window)? UC and
  Pension Credit conventions suggest the former.
- The auto-payment for Core Group 1 means the rebate is functionally
  irreversible — it doesn't depend on the household applying. Does the
  model need a `would_claim_warm_home_discount` flag at all for Core 1,
  or should it just be `defined_for = "has_pension_credit_guarantee_credit"`?
  Recommendation: skip the take-up gate for Core 1.

## References

- [Warm Home Discount Scheme: official guidance](https://www.gov.uk/the-warm-home-discount-scheme).
- [Warm Home Discount (England and Wales) Regulations 2022 (SI 2022/687)](https://www.legislation.gov.uk/uksi/2022/687/contents) — the 2022-23 reform that introduced the EPC-based England Core Group 2.
- [Warm Home Discount (Scotland) Regulations 2022 (SI 2022/690)](https://www.legislation.gov.uk/uksi/2022/690/contents) — devolved variant.
- Ofgem, [Warm Home Discount Scheme: annual reports][gov-2022].
- Issue: [#502](https://github.com/PolicyEngine/policyengine-uk/issues/502).

[gov-2022]: https://www.ofgem.gov.uk/publications/warm-home-discount-annual-reports
