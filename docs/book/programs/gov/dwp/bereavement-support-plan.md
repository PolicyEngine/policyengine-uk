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
Updated October 2026: still reported-only; the facts below were checked
against GOV.UK and legislation.gov.uk, and the data notes now describe
Microcosm UK, the current UK data pipeline.
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
- The legacy WPA has no variable of its own. Microcosm UK fills
  `bsp_reported` from FRS benefit codes 6 and 9
  ([`frs_spine.py`](https://github.com/PolicyEngine/microcosm/blob/75167a68/packages/microcosm-build/src/microcosm/build/uk_runtime/frs_spine.py#L825)),
  and Microcosm's own source notes say code 6 mixes benefits and code 9
  is War Widow's Pension. So the reported "BSP" also carries legacy
  widow's benefits and War Widow's Pension.

## Proposed scope

### Phase 1 — BSP rule-based formula

The BSP under the [Pensions Act 2014, Part 5][pa-2014-5] and the
[Bereavement Support Payment Regulations 2017][bsp-regs] (SI 2017/410)
pays:

- A **lump-sum** of either £2,500 (Standard Rate) or £3,500 (Higher
  Rate, with a dependent child).
- **18 monthly payments** of £100 (Standard) or £350 (Higher), for a
  death on or after 6 April 2017
  ([GOV.UK](https://www.gov.uk/bereavement-support-payment/what-youll-get)).

The Higher Rate applies if, when the partner died, the claimant was
getting (or entitled to) Child Benefit for a child living with them, or
was pregnant. The
[Bereavement Benefits (Remedial) Order 2023](https://www.legislation.gov.uk/uksi/2023/134/contents)
(SI 2023/134) extended BSP and WPA to cohabiting partners with
children, with effect back to 30 August 2018, after the Supreme Court's
2018 McLaughlin judgment. It didn't change the number of payments.

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
Benefits Act 1992 s. 39A][sscba-39a]) was paid for deaths from April
2001 to 5 April 2017. The benefit:

- Continued for as long as the surviving spouse had a dependent child.
- Was uprated annually.
- Was replaced by BSP for deaths from 6 April 2017.

For historical analyses the model should:

- Add `wpa_eligible` (Person, YEAR) — bereavement date 2001-04 to
  2017-04 inclusive, with a dependent child.
- Add `widowed_parents_allowance` (Person, YEAR) as a derived
  formula reading the WPA rate parameter (which would need
  backfilling under `gov/dwp/wpa/rate.yaml`).

WPA has no new awards, but existing awards continue while the
surviving parent has a dependent child, so some recipients remain. In
the current data they sit inside `bsp_reported` (see above), so they
are already counted in income; the gap is that they can't be told
apart from BSP or reformed separately.

### Phase 3 — data-side bereavement flag

`is_bereaved_recently` doesn't exist in the FRS. The FRS is a
cross-section, not a panel, and doesn't record when a partner died, so
the flag would need imputing in Microcosm UK:

- start from FRS respondents who report BSP (once it is separated from
  the other codes, as above) and from widowed respondents;
- calibrate to DWP's BSP and WPA caseloads ([Stat-Xplore](https://stat-xplore.dwp.gov.uk/)) by age, sex
  and region.

This is the heaviest of the three phases; without it the new
variables work for the household-calculator (which can input the flag
directly) but not for microsim aggregates.

## Open questions

- BSP isn't uprated each year. The rates have been £2,500/£3,500 and
  £100/£350 since 2017.
  Should the parameter tree carry an explicit
  `uprating: gov.economic_assumptions.indices.obr.consumer_price_index`
  to mirror what other DWP rates do, or hold flat to match the
  historical reality?
- WPA recipients who would have been on BSP under the new rules: do we
  want a reform-side parameter "treat all WPA receipts as if they were
  BSP" for counterfactual analysis?
- The 2023 Remedial Order extended BSP to cohabiting partners with
  children, with effect from 30 August 2018. Eligibility should not
  require marriage or civil partnership for deaths from that date where
  there are children.

## References

- [Pensions Act 2014, Part 5](https://www.legislation.gov.uk/ukpga/2014/19/part/5) — primary statute for BSP.
- [Bereavement Support Payment Regulations 2017 (SI 2017/410)][bsp-regs].
- [Bereavement Benefits (Remedial) Order 2023 (SI 2023/134)](https://www.legislation.gov.uk/uksi/2023/134/contents) — cohabiting-parent extension, effective from 30 August 2018.
- [SSCBA 1992 s. 39A][sscba-39a] — legacy WPA basis.
- gov.uk, [Bereavement Support Payment](https://www.gov.uk/bereavement-support-payment) and [Widowed Parent's Allowance](https://www.gov.uk/widowed-parents-allowance).
- DWP, [Stat-Xplore](https://stat-xplore.dwp.gov.uk/): Bereavement Support Payment and Widowed Parent's Allowance caseloads.
- Issues: [#466](https://github.com/PolicyEngine/policyengine-uk/issues/466) (BSP formula), [#465](https://github.com/PolicyEngine/policyengine-uk/issues/465) (historical WPA).

[pa-2014-5]: https://www.legislation.gov.uk/ukpga/2014/19/part/5
[bsp-regs]: https://www.legislation.gov.uk/uksi/2017/410/contents
[sscba-39a]: https://www.legislation.gov.uk/ukpga/1992/4/section/39A
