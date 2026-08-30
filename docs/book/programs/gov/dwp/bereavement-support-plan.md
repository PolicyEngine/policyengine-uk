# Bereavement support: BSP formula and historical WPA (planned)

```{warning}
**Currently reported-only.** PolicyEngine UK models the Bereavement
Support Payment (BSP) as `adds = ["bsp_reported"]` — i.e. the value
flows through from the dataset, with no derived eligibility or
rule-based amount. This page captures the proposed formula-based
extension covering both BSP and the legacy Widowed Parent's Allowance
(WPA) for historical analysis. Tracks
[#466](https://github.com/PolicyEngine/policyengine-uk/issues/466) and
the related historical-WPA ask in
[#465](https://github.com/PolicyEngine/policyengine-uk/issues/465).
```

## What's currently modelled

Just the FRS-reported amount:

```python
class bsp(Variable):
    label = "Bereavement Support Payment"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["bsp_reported"]
```

That means:

- Reform analyses changing BSP rates have no household-level surface.
- Anyone bereaved after the FRS reference week never appears as a BSP
  recipient even if eligible.
- The legacy WPA is not modelled at all — anyone reporting it in
  historical FRS waves drops into the residue.

## Proposed scope

### Phase 1 — BSP rule-based formula

The BSP under the [Pensions Act 2014, Part 5][pa-2014-5] and the
[Bereavement Support Payment Regulations 2017][bsp-regs] (SI 2017/410)
pays:

- A **lump-sum** of either £2,500 (Standard Rate) or £3,500 (Higher
  Rate, with a dependent child).
- A **monthly payment** of £100 (Standard) or £350 (Higher) for up to
  **18 monthly instalments** after a death on or after 6 April 2017
  (extended from 12 months by the Bereavement Benefits
  (Remedial) Order 2023, SI 2023/134, after the McLaughlin / Jackson
  ECHR rulings).

To model this we need:

- `is_bereaved_recently` (Person, YEAR) — a new input flagging
  whether the person has been bereaved in the last 18 months.
- `bsp_higher_rate_eligible` (Person, YEAR) — whether they have a
  dependent child.
- `bsp_months_remaining` (Person, YEAR) — how many of the 18 monthly
  instalments fall within the simulation year.

The BSP formula then becomes:

```
bsp = (
    lump_sum_amount * is_bereaved_recently
    + monthly_amount * bsp_months_remaining
)
```

Both `lump_sum_amount` and `monthly_amount` parameter trees split on
`bsp_higher_rate_eligible` (£3,500 / £350 vs £2,500 / £100).

### Phase 2 — WPA (historical) under the same formula

Widowed Parent's Allowance (under [Social Security Contributions and
Benefits Act 1992 s. 39A][sscba-39a]) was paid for deaths between
April 2001 and 5 April 2017. The benefit:

- Continued for as long as the surviving spouse had a dependent child.
- Was uprated annually.
- Was replaced by BSP for deaths from 6 April 2017.

For historical analyses the model should:

- Add `wpa_eligible` (Person, YEAR) — bereavement date 2001-04 to
  2017-04 inclusive, with a dependent child.
- Add `widowed_parents_allowance` (Person, YEAR) as a derived
  formula reading the WPA rate parameter (which would need
  backfilling under `gov/dwp/wpa/rate.yaml`).

WPA receipts are now a closing tail of the recipient pool (no new
awards) but still appear in current FRS waves; the present model
treats those as a generic `maintenance_income`-class residue. Closing
this gap improves the alignment of HBAI net income for the few
thousand remaining recipients.

### Phase 3 — data-side bereavement flag

`is_bereaved_recently` doesn't exist in the FRS as a clean field; it
would need imputing in `policyengine-uk-data` from:

- the FRS marital-status code transitions between waves (widowed in
  current wave but not in the previous wave),
- DWP BSP/WPA caseload by region by year as the calibration target.

This is the heaviest of the three phases; without it the new
variables work for the household-calculator (which can input the flag
directly) but not for microsim aggregates.

## Open questions

- BSP is currently uprated discretionarily rather than by statute. The
  monthly rate has been £100/£350 since 2017 with no annual uprating.
  Should the parameter tree carry an explicit
  `uprating: gov.economic_assumptions.indices.obr.consumer_price_index`
  to mirror what other DWP rates do, or hold flat to match the
  historical reality?
- WPA recipients who would have been on BSP under the new rules: do we
  want a reform-side parameter "treat all WPA receipts as if they were
  BSP" for counterfactual analysis?
- The McLaughlin / Jackson ECHR rulings extended BSP to cohabiting
  partners with children from 9 February 2023. The current
  `bsp_higher_rate_eligible` rule should encode this in its
  effective-date logic.

## References

- [Pensions Act 2014, Part 5](https://www.legislation.gov.uk/ukpga/2014/19/part/5) — primary statute for BSP.
- [Bereavement Support Payment Regulations 2017 (SI 2017/410)][bsp-regs].
- [Bereavement Benefits (Remedial) Order 2023 (SI 2023/134)](https://www.legislation.gov.uk/uksi/2023/134/contents) — cohabiting-parent extension and 18-month limit.
- [SSCBA 1992 s. 39A][sscba-39a] — legacy WPA basis.
- gov.uk, [Bereavement Support Payment](https://www.gov.uk/bereavement-support-payment) and [Widowed Parent's Allowance](https://www.gov.uk/widowed-parents-allowance).
- DWP, [Bereavement support statistics](https://www.gov.uk/government/collections/dwp-statistical-summaries-on-bereavement-payments).
- Issues: [#466](https://github.com/PolicyEngine/policyengine-uk/issues/466) (BSP formula), [#465](https://github.com/PolicyEngine/policyengine-uk/issues/465) (historical WPA).

[pa-2014-5]: https://www.legislation.gov.uk/ukpga/2014/19/part/5
[bsp-regs]: https://www.legislation.gov.uk/uksi/2017/410/contents
[sscba-39a]: https://www.legislation.gov.uk/ukpga/1992/4/section/39A
