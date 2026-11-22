# Bereavement support: BSP formula and historical WPA (planned)

```{warning}
**Currently reported-only.** PolicyEngine UK models the Bereavement
Support Payment (BSP) as `adds = ["bsp_reported"]`, so the value
flows through from the dataset, with no derived eligibility or
rule-based amount. This page captures the proposed formula-based
extension covering both BSP and the legacy Widowed Parent's Allowance
(WPA) for historical analysis. Tracks
[#466](https://github.com/PolicyEngine/policyengine-uk/issues/466) and
the related historical-WPA ask in
[#465](https://github.com/PolicyEngine/policyengine-uk/issues/465).
Updated October 2026: still reported-only; the facts below were checked
against GOV.UK and legislation.gov.uk. The data notes cover both the
Enhanced FRS (policyengine-uk-data, which policyengine-uk's own tests
still pin at 1.58.1) and Microcosm UK, which replaced it as the certified
default UK dataset in policyengine.py 6.10.0 (21 October 2026).
```

## What's currently modelled

Just the FRS-reported amount:

```python
class bsp(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment"
    definition_period = YEAR
    unit = GBP

    adds = ["bsp_reported"]
```

That means:

- Reform analyses changing BSP rates have no household-level surface.
- Anyone bereaved after the FRS reference week never appears as a BSP
  recipient even if eligible.
- The Enhanced FRS
  ([`frs.py`](https://github.com/PolicyEngine/policyengine-uk-data/blob/main/policyengine_uk_data/datasets/frs.py))
  fills `bsp_reported` from FRS benefit codes 6 and 9, and so did
  Microcosm UK up to its certified 19 October 2026 build
  ([`frs_spine.py`](https://github.com/PolicyEngine/microcosm/blob/75167a68/packages/microcosm-build/src/microcosm/build/uk_runtime/frs_spine.py#L825));
  Microcosm's own
  [source notes](https://github.com/PolicyEngine/microcosm/blob/d1fda720/packages/microcosm-build/src/microcosm/build/uk/spec/sources.yaml#L1870)
  say code 6 mixes benefits and code 9 is tax-free War Widow's Pension.
  The FRS labels code 6 "Bereavement Support Payment / Widowed Parent's
  Allowance" and code 9 "War Widow's/Widower's Pension", so wherever both
  codes are summed the reported "BSP" also carries Widowed Parent's
  Allowance and War Widow's Pension. Microcosm's main branch now puts
  code 9 in `war_widows_pension_reported` and keeps only code 6 in
  `bsp_reported`
  ([microcosm#1333](https://github.com/PolicyEngine/microcosm/pull/1333)).
- Since [#2382](https://github.com/PolicyEngine/policyengine-uk/pull/2382)
  (2.135.7), War Widow's Pension has its own variables,
  `war_widows_pension_reported` and `war_widows_pension`. `bsp_reported`
  stays nominally flat for datasets that explicitly supply both
  `war_widows_pension_reported` and `widowed_parents_allowance_reported`
  in the same source year, including all-zero columns. Datasets with
  either column missing retain CPI uprating, as do household situations.
  Microcosm's merged
  [#1383](https://github.com/PolicyEngine/microcosm/pull/1383) supplies both
  columns and closes
  [#1222](https://github.com/PolicyEngine/microcosm/issues/1222). Older
  releases and the Enhanced FRS retain the compatibility path;
  [policyengine-uk-data#578](https://github.com/PolicyEngine/policyengine-uk-data/issues/578)
  tracks the Enhanced FRS code-9 move. See the
  [dataset-source guide](https://github.com/PolicyEngine/policyengine-uk/blob/main/docs/engineering/skills/dataset-sources.md#bereavement-benefit-split)
  for projection, fallback and off-rate residual treatment.
- Since [#2572](https://github.com/PolicyEngine/policyengine-uk/issues/2572),
  WPA also has its own variables, `widowed_parents_allowance_reported`
  (CPI-uprated) and `widowed_parents_allowance`. Unlike BSP, WPA is taxable
  ([ITEPA 2003 s. 577](https://www.legislation.gov.uk/ukpga/2003/1/section/577)),
  Universal Credit unearned income
  ([UC Regulations 2013 reg. 66(1)(b)(vi)](https://www.legislation.gov.uk/uksi/2013/376/regulation/66)),
  pension income for tax credits, where the model ignores the first £300 a
  year of its pension, investment and property income together (the law also
  adds foreign and notional income to that total)
  ([SI 2002/2006 reg. 3](https://www.legislation.gov.uk/uksi/2002/2006/regulation/3)
  and [reg. 5(1)(a)](https://www.legislation.gov.uk/uksi/2002/2006/regulation/5)),
  Income Support income less £10 a week
  ([IS Regulations 1987 Sch. 9 para. 16(h)](https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/16)),
  Housing Benefit income less £15 a week (less £10 on the
  savings-credit-only route below)
  ([HB Regulations 2006 Sch. 5 para. 16](https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/16);
  [HB (SPC) Regulations 2006 Sch. 5 para. 7](https://www.legislation.gov.uk/uksi/2006/214/schedule/5/paragraph/7)),
  a welfare benefit for the benefit cap and an overlapping benefit for Carer's Allowance and Carer Support
  Payment. The model counts it less £15 a week in Council Tax Reduction
  too (less £10 on that route), but for working-age applicants with
  Universal Credit it counts it in full in Wales and in the five English
  council schemes it holds (Merton, Kingston upon Thames, Newham and
  Westminster, and Oxford from April 2026). Elsewhere in England the model
  uses a working-age applicant's reported reduction, capped at their share
  of a jointly liable bill when another claim in the household is paid a
  simulated reduction and no one counted in the share may be a student. The
  model leaves WPA out of Scotland's working-age scheme, and out of the
  Welsh one for applicants without Universal Credit, although both count
  it less £15 a week, and Wales also disregards the income tax on it
  ([SSI 2021/249 reg. 57(1)(b)(vi) and (4)](https://www.legislation.gov.uk/ssi/2021/249/regulation/57);
  [WSI 2013/3029 Sch. 6 para. 17](https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/17),
  [Sch. 9 para. 4](https://www.legislation.gov.uk/wsi/2013/3029/schedule/9/paragraph/4)
  and [para. 21](https://www.legislation.gov.uk/wsi/2013/3029/schedule/9/paragraph/21)).
  [#2931](https://github.com/PolicyEngine/policyengine-uk/issues/2931) tracks the fix. The model also counts WPA in a
  non-dependant's gross income for the Housing Benefit non-dependant
  deduction and the English pension-age, Scottish and Welsh Council Tax
  Reduction ones, but not in the five English council schemes. WPA ends at
  State Pension age or when the recipient marries or forms a new civil or
  cohabiting partnership, and is not paid while the recipient lives with
  someone as a couple ([SSCBA 1992 s. 39A(4) to (5)][sscba-39a]).
  Pension Credit's qualifying age is women's State Pension age
  ([State Pension Credit Act 2002 s. 1(6)](https://www.legislation.gov.uk/ukpga/2002/16/section/1)),
  so until December 2018 a widower between that age and 65 could get both,
  and Pension Credit counts WPA less £10 a week
  ([State Pension Credit Regulations 2002 Sch. IV para. 7](https://www.legislation.gov.uk/uksi/2002/1792/schedule/IV/paragraph/7)).
  Since then no one can get both, but the model still counts a reported
  award in Pension Credit, less £10 a week, and uses that Pension Credit
  figure in Housing Benefit and Council Tax Reduction for a
  savings-credit-only award. Older datasets still put it in `bsp_reported`;
  Microcosm #1383 separates amounts matching its positive WPA rate rule,
  while retaining unclassified off-rate amounts in BSP.

## Proposed scope

### Phase 1: rule-based BSP formula

The BSP under the [Pensions Act 2014, Part 5][pa-2014-5] and the
[Bereavement Support Payment Regulations 2017][bsp-regs] (SI 2017/410)
pays:

- A **lump sum** of either £2,500 (standard rate) or £3,500 (higher
  rate), paid only if the claim is made within 12 months of the death
  (SI 2017/410 reg 3(2) and (5)).
- Up to **18 monthly payments** of £100 (standard) or £350 (higher), all
  18 only if the claim is made within 3 months of the death
  ([GOV.UK](https://www.gov.uk/bereavement-support-payment/what-youll-get)),
  for a death on or after 6 April 2017, when Pensions Act 2014 s. 30 came
  fully into force. Someone who reaches State Pension age within 18
  months of the death may get fewer.

The higher rate applies if the claimant was pregnant or entitled to
Child Benefit when the partner died, or later became entitled to Child
Benefit for a child who lived with them or the partner immediately
before the death (SI 2017/410 reg 4). The
[Bereavement Benefits (Remedial) Order 2023](https://www.legislation.gov.uk/uksi/2023/134/contents)
(SI 2023/134) extended BSP and WPA to cohabiting partners with
children, with effect back to 30 August 2018, after the Supreme Court's
2018 McLaughlin judgment (on WPA) and the High Court's 2020 Jackson
judgment (on BSP). It kept the 18-month maximum, but a cohabiting
partner whose partner died between 6 April 2017 and 29 August 2018 gets
18 monthly payments less one for each month that had passed by
29 August 2018 (SI 2017/410 reg 2(7) to (11)).

To model this we need:

- `bsp_initial_payment_due` (Person, YEAR): a new input that is true
  only in the year the BSP claim is made after the partner's death, so
  the [single initial payment](https://www.gov.uk/bereavement-support-payment/what-youll-get)
  is paid once. A flag for "bereaved in the last 18 months" would stay
  true across two consecutive annual periods and pay the lump sum twice.
- `bsp_higher_rate_eligible` (Person, YEAR): whether they were pregnant
  or entitled to Child Benefit when the partner died, or became entitled
  afterwards for a child who lived with them or the partner
  (SI 2017/410 reg 4).
- `bsp_months_remaining` (Person, YEAR): how many of the 18 monthly
  instalments fall within the simulation year (0 to 12). This is where
  the 18-month window belongs.

The BSP formula then becomes:

```
bsp = (
    lump_sum_amount * bsp_initial_payment_due
    + monthly_amount * bsp_months_remaining
)
```

An alternative is a single date-of-death (or claim-date) input from
which both the initial-payment year and the months in each year are
derived. Either way the lump sum is tied to one year only.

Both `lump_sum_amount` and `monthly_amount` parameter trees split on
`bsp_higher_rate_eligible` (£3,500 / £350 vs £2,500 / £100).

These parameters should be held flat, with no `uprating` key. BSP is
not uprated: the four amounts in [SI 2017/410 reg 3][bsp-reg-3] have
been £350, £3,500, £100 and £2,500 since April 2017, and the
[Social Security Benefits Up-rating Order 2026][uprating-2026]
(SI 2026/148), art 19, says each of them "remains unchanged".

### Phase 2: historical WPA under the same formula

Widowed Parent's Allowance (under [Social Security Contributions and
Benefits Act 1992 s. 39A][sscba-39a]) is paid for deaths before 6 April
2017 (s. 39A(1)(a)), except where a woman's husband died before 9 April
2001 (s. 39A(1A)). The benefit:

- Continues while the survivor is entitled to Child Benefit for a
  qualifying child (or is pregnant) and is under State Pension age, and
  ends on remarriage or a new civil or cohabiting partnership
  (s. 39A(4) and (5)).
- Is uprated each April (£156.65 a week from April 2026, SI 2026/148
  art 18).
- Was replaced by BSP for deaths from 6 April 2017.

For historical analyses the model should:

- Add `wpa_eligible` (Person, YEAR): the partner died before 6 April
  2017 (but not a woman's husband before 9 April 2001), the partner met
  the contribution conditions, and the survivor is under State Pension
  age, has not remarried or formed a new partnership, and is entitled to
  Child Benefit for a qualifying child or is pregnant (SSCBA 1992
  s. 39A).
- Replace the `adds` of `widowed_parents_allowance` (Person, YEAR) with
  a formula reading the WPA rate parameter (which would need
  backfilling under `gov/dwp/wpa/rate.yaml`).

WPA is closed to deaths from 6 April 2017, but new claims for earlier
deaths are still possible
([GOV.UK](https://www.gov.uk/widowed-parents-allowance)): the 2023 Remedial Order brought about 3,400
successful WPA claims from cohabiting partners between February 2023 and
November 2024
([DWP, July 2025](https://www.gov.uk/government/publications/bereavement-benefit-remedial-order-uptake-february-2023-to-november-2024)).
Existing awards continue while the surviving parent is entitled to Child
Benefit and under State Pension age, so some recipients remain. In
older datasets they sit inside `bsp_reported` (see above), so they are
already counted in income. Datasets that fill
`widowed_parents_allowance_reported` distinguish those reported amounts
from BSP; the gap left is a rule-based amount for reforms.

### Phase 3: data-side bereavement inputs

Neither `bsp_initial_payment_due` nor `bsp_months_remaining` exists in
the FRS. The FRS is a cross-section, not a panel, and its benefits
documentation shows no record of when a partner died, so these inputs
would need imputing in the data (Microcosm UK, now the certified default
UK dataset):

- start from FRS respondents who report BSP (once it is separated from
  the other codes, as above) and from widowed respondents;
- calibrate to DWP's BSP caseloads ([Stat-Xplore](https://stat-xplore.dwp.gov.uk/),
  by age, gender and geography, from April 2017) and to WPA caseloads
  where DWP still publishes them.

This is the heaviest of the three phases; without it the new
variables work for the household calculator (which can input them
directly) but not for microsim aggregates.

## Open questions

- WPA recipients who would have been on BSP under the new rules: do we
  want a reform-side parameter "treat all WPA receipts as if they were
  BSP" for counterfactual analysis?
- The 2023 Remedial Order extended BSP to cohabiting partners, with
  effect from 30 August 2018. Eligibility should not require marriage or
  civil partnership where the survivor was pregnant or entitled to Child
  Benefit (Pensions Act 2014 s. 30(1)(aa)), for deaths on or after
  6 April 2017; for deaths before 30 August 2018 the monthly payments
  are cut as in SI 2017/410 reg 2(7) to (11).

## References

- [Pensions Act 2014, Part 5](https://www.legislation.gov.uk/ukpga/2014/19/part/5): primary statute for BSP.
- [Bereavement Support Payment Regulations 2017 (SI 2017/410)][bsp-regs].
- [Social Security Benefits Up-rating Order 2026 (SI 2026/148), art 19][uprating-2026]: holds the four BSP amounts unchanged.
- [Bereavement Benefits (Remedial) Order 2023 (SI 2023/134)](https://www.legislation.gov.uk/uksi/2023/134/contents): cohabiting-parent extension, effective from 30 August 2018.
- [SSCBA 1992 s. 39A][sscba-39a]: legacy WPA basis.
- gov.uk, [Bereavement Support Payment](https://www.gov.uk/bereavement-support-payment) and [Widowed Parent's Allowance](https://www.gov.uk/widowed-parents-allowance).
- DWP, [Stat-Xplore](https://stat-xplore.dwp.gov.uk/): Bereavement Support Payment claims and recipients from April 2017.
- DWP, [Uptake of backdated BSP and WPA under the Bereavement Benefits (Remedial) Order 2023](https://www.gov.uk/government/publications/bereavement-benefit-remedial-order-uptake-february-2023-to-november-2024) (July 2025).
- Issues: [#466](https://github.com/PolicyEngine/policyengine-uk/issues/466) (BSP formula), [#465](https://github.com/PolicyEngine/policyengine-uk/issues/465) (historical WPA).

[pa-2014-5]: https://www.legislation.gov.uk/ukpga/2014/19/part/5
[bsp-regs]: https://www.legislation.gov.uk/uksi/2017/410/contents
[bsp-reg-3]: https://www.legislation.gov.uk/uksi/2017/410/regulation/3
[uprating-2026]: https://www.legislation.gov.uk/uksi/2026/148/article/19
[sscba-39a]: https://www.legislation.gov.uk/ukpga/1992/4/section/39A
