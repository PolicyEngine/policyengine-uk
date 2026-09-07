# Firm-level VAT (planned)

```{warning}
**Not yet modelled.** PolicyEngine UK currently models VAT only at the
*household consumption* level (the `vat` variable, computed from
consumption-category spending and rate parameters under
`gov.hmrc.vat`). This page captures the agreed scope and roadmap for
adding firm-level VAT and a new `Firm` entity, tracked under
[#1320](https://github.com/PolicyEngine/policyengine-uk/issues/1320) and
[#1333](https://github.com/PolicyEngine/policyengine-uk/issues/1333). It
mirrors the [BiK plan](./benefits-in-kind.md) pattern.
```

## Why firm-level VAT?

Household-side VAT in PolicyEngine answers the question "what does this
household pay in VAT on the goods and services it buys?" but it can't
answer policy questions framed at the business side:

- How does changing the VAT registration threshold (currently £90,000
  annual turnover) affect the number of firms in scope, and through
  them the consumer prices that households face?
- What's the revenue effect of moving a supply between standard, reduced
  and zero rates seen from the *supplier* side (input/output netting)?
- How does the flat-rate scheme distort the modelled compliance picture?

Closing those questions needs a separate entity that *carries* turnover,
sector, and registration status, and variables for input/output VAT and
net liability.

## Scope

### Phase 1 — MVP

1. **`Firm` entity** with the bare attributes needed for the threshold
   and rate questions: `firm_turnover`, `firm_industry_sector`,
   `firm_vat_registered`. Firms are linked to households for sole
   traders and partnerships (unincorporated business income flows
   already exist in the FRS) and stand alone for incorporated entities.
2. **Registration threshold logic**: a firm is VAT-registered if
   turnover meets or exceeds `gov.hmrc.vat.registration_threshold` (or
   the firm has elected to register voluntarily). Threshold currently
   £90,000 since April 2024.
3. **Standard / reduced / zero-rated supply split** at the firm level,
   driven by sector-specific share parameters.
4. **`firm_vat_on_sales`** (output VAT) and **`firm_vat_on_purchases`**
   (input VAT), each computed from share-based decompositions of
   turnover and intermediate consumption.
5. **`firm_net_vat_liability`** = output VAT − input VAT.

### Phase 2 — distributional refinements

- **Flat-rate scheme** for small businesses (`gov.hmrc.vat.flat_rate_scheme/`).
- **VAT groups** and partial exemption (de minimis rules for
  exempt-versus-taxable splits).
- **Cross-border VAT** post-Brexit changes (Northern Ireland Protocol,
  postponed accounting).

### Phase 3 — incidence

- **Pass-through** of VAT rate changes to consumer prices, joining up
  the household-side `vat` variable and the firm-side
  `firm_net_vat_liability` through an explicit incidence assumption
  (already modelled in spirit via `vat_change` on the household side;
  Phase 3 promotes it to a first-class link).

## Implementation plan

### Entity

A new `Firm` entity in `policyengine_uk/entities.py` next to the
existing `Household`, `BenUnit`, `Person`:

```python
Firm = build_entity(
    key="firm",
    plural="firms",
    label="Firm",
    doc="A business entity that may register for VAT.",
    roles=[{"key": "owner", "plural": "owners",
            "label": "Owner",
            "doc": "Person or household that owns the firm."}],
    containing_entities=["state"],
)
```

The `containing_entities` set deliberately does *not* include
`household` because incorporated firms have no household; the link for
sole traders is via an explicit `firm_owning_household_id` input
variable rather than entity nesting.

### Variables

Under a new `variables/gov/hmrc/vat/firm/` tree:

- `firm_turnover` (input)
- `firm_industry_sector` (input, enum)
- `firm_vat_registered` (derived from turnover and the threshold; can
  also be set as input for voluntary registration)
- `firm_standard_rated_share`, `firm_reduced_rated_share`,
  `firm_zero_rated_share`, `firm_exempt_share` (derived from sector or
  input override)
- `firm_vat_on_sales` (output VAT)
- `firm_vat_on_purchases` (input VAT)
- `firm_net_vat_liability` (output − input)

The household-side `vat` variable stays untouched; the two sides only
meet in Phase 3.

### Parameters

A new tree under `parameters/gov/hmrc/vat/firm/`:

- `registration_threshold.yaml` — currently £90,000 from April 2024.
- `deregistration_threshold.yaml` — currently £88,000 from April 2024.
- `rates/standard.yaml`, `reduced.yaml`, `zero.yaml` — these already
  exist on the household-side tree and will be referenced rather than
  duplicated.
- `sector_supply_split/` — share parameters by industry sector for the
  standard/reduced/zero/exempt split (Phase 1.5 refinement; MVP can use
  a single national split per sector).
- `flat_rate_scheme/` — Phase 2.

### Tests

- Unit tests around the threshold (firm just below, just above, just
  above the deregistration threshold).
- Tests of rate-split arithmetic for each sector.
- Integration test asserting that summing `firm_net_vat_liability`
  across a representative firm panel reproduces published HMRC VAT
  receipts to within calibration tolerance.

## Data needs

This is the harder half of the project. Summary of where each Phase 1
component sits w.r.t. our current data:

| Component | Public source | FRS coverage | Datalab source |
|-----------|---------------|--------------|----------------|
| Firm turnover distribution | ONS *Business Demography* | sole-trader / partnership turnover via FRS self-employment income | HMRC Datalab — anonymised VAT returns |
| Industry sector | SIC codes from ONS *Inter-Departmental Business Register (IDBR)* | not in FRS | HMRC Datalab |
| VAT registration share | HMRC *VAT statistics* (annual) | not in FRS | HMRC Datalab |
| Input VAT shares | ONS *Supply and Use tables* | not applicable | HMRC Datalab |

### Proposed imputation approach

1. Build a **synthetic firm panel** weighted to ONS Business Demography
   counts by SIC sector and turnover band.
2. Attach to each firm a registration status, supply split, and
   intermediate-consumption ratio drawn from HMRC VAT statistics and
   ONS Supply and Use tables.
3. Calibrate the panel so that summed `firm_net_vat_liability` matches
   the HMRC VAT receipts outturn for the year. This mirrors the
   second-stage imputation pattern flagged in
   [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621).
4. For sole traders and partnerships, link the synthetic firm row back
   to the FRS household that owns it via self-employment income.

The companion repo [`policyengine/uk-vatlab`][vatlab] hosts the analysis
files (#1333) used to size each step before they are productionised.

## Effort estimate

- Adding the `Firm` entity, `firm_turnover` input, threshold logic, and
  a single-rate liability variable: ~1–2 days.
- Phase 1 MVP (full Firm entity, sector-driven supply split, calibrated
  synthetic firm panel, threshold/rate tests, integration test against
  HMRC outturn): ~3–4 weeks, with most time on the data side.
- Phase 2 (flat-rate scheme, VAT groups, partial exemption): another
  2–3 weeks once the panel is stable.
- Phase 3 (cross-side incidence): tied to the
  `consumer_incident_tax_revenue_change` infrastructure already in the
  repo; the link itself is small but the elasticity assumptions need
  agreement.

## Open questions

- Should the synthetic firm panel live in `policyengine-uk-data` (matching
  the FRS calibration pipeline) or in this repo? Recommendation: it
  belongs in `policyengine-uk-data`, with the rules variables here.
- Do we need to model Making Tax Digital filing-frequency mechanics, or
  is annualised liability sufficient for nowcasting purposes?
- HMRC Datalab access for anonymised VAT returns: pursue, or stick to
  ONS / public-aggregate calibration?

## References

- HMRC, [VAT rates](https://www.gov.uk/vat-rates) and [VAT registration thresholds](https://www.gov.uk/vat-registration-thresholds).
- [Value Added Tax Act 1994](https://www.legislation.gov.uk/ukpga/1994/23/contents) — primary statute.
- HMRC, [VAT statistics](https://www.gov.uk/government/collections/value-added-tax-vat-statistics) — annual outturn used for calibration.
- ONS, [UK Business: Activity, Size and Location](https://www.ons.gov.uk/businessindustryandtrade/business/activitysizeandlocation) (the IDBR-based business demography release).
- ONS, [Supply and Use tables](https://www.ons.gov.uk/economy/nationalaccounts/supplyandusetables) — intermediate consumption shares.
- Companion analysis repo: [`policyengine/uk-vatlab`][vatlab] (#1333).

[vatlab]: https://github.com/policyengine/uk-vatlab
