# Regional childcare programmes (planned)

```{warning}
**Partially modelled.** PolicyEngine UK models the **England** funded
childcare programmes (Universal, Extended and Targeted Childcare
Entitlements; Care to Learn; Student Finance England Childcare Grant)
and the **UK-wide** Tax-Free Childcare scheme. The devolved
administrations operate parallel schemes that are not yet modelled
beyond the Scottish Universal Funded ELC for 3- and 4-year-olds added
in [#1643][pr-1643]. This page captures the proposed scope, tracked
under [#1008](https://github.com/PolicyEngine/policyengine-uk/issues/1008)
and the broader [#1644 audit][issue-1644].
```

## What is modelled today

The current childcare coverage is captured in
[`policyengine_uk/programs.yaml`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/programs.yaml) (see the
[#1644 split into per-programme rows][issue-1644]) and works as follows:

- **UK-wide**: Tax-Free Childcare (HMRC); Universal Credit childcare
  element (DWP); Working Tax Credit childcare element (legacy, HMRC
  administered, modelled under `gov/dwp/`; see
  [tax-credits.md](./../dwp/tax-credits.md)).
- **England-only** (gate on `country == ENGLAND`):
  Universal Childcare Entitlement (15 hours for 3- and 4-year-olds),
  Extended Childcare Entitlement (working parents, now reaching down to
  children aged nine months), Targeted Childcare Entitlement (2-year-olds
  in families on qualifying benefits or low incomes), Care to Learn,
  Student Finance England Childcare Grant.
- **Scotland**: eligibility for the universal funded ELC for 3- and
  4-year-olds (`scottish_funded_early_learning_childcare_eligible`,
  including the statutory start-date rule for 3-year-olds) and its 1,140
  hours a year, added in [#1643][pr-1643]. No funding value is attached
  yet, so it does not reach household income.
- **Wales, Northern Ireland**: no programmes modelled.

## Proposed scope by jurisdiction

### Scotland: three remaining strands

The [#1644 audit][issue-1644] flagged three Scottish gaps:

1. **Eligible-two-year-old strand** of the funded ELC programme
   (vulnerable or low-income 2-year-olds under the
   [Provision of Early Learning and Childcare (Specified Children)
   (Scotland) Order 2014][sssi-196-2014]). Modelled the same way as the
   3- and 4-year-old strand but gated on UC, tax credits or other
   qualifying benefits.
2. **Student Awards Agency Scotland (SAAS) Lone Parents' Grant,
   Dependants' Grant, and Childcare Fund** for full-time HE students:
   the Scottish equivalent of Student Finance England's Childcare
   Grant. Income-tested.
3. **Support for young parents in further education**, the role Care to
   Learn plays in England. The [Education Maintenance Allowance][scot-ema]
   still runs in Scotland for 16- to 19-year-olds, applied for through
   local councils and colleges, but it is a maintenance payment rather
   than childcare support, so the childcare side needs its own scoping.

### Wales

The audit identified four Welsh programmes:

1. **Childcare Offer for Wales**: 30 hours a week for working parents
   of 3- and 4-year-olds (term time plus some holiday weeks).
   Modelled the same as the English Extended Childcare Entitlement
   with Welsh-specific income tests and hour caps. Statutory basis:
   [Childcare Funding (Wales) Act 2019][wales-act].
2. **Flying Start**: a universal offer in disadvantaged areas for
   2- to 3-year-olds (12.5 hours a week). Eligibility is geographic,
   based on lower layer super output areas.
3. **Student Finance Wales Childcare Grant**, parallel to the English
   Childcare Grant.
4. **Welsh EMA**, parallel to the Scottish EMA.

### Northern Ireland

The audit identified four NI programmes:

1. **Pre-school Education Programme (PSEP)**: 12.5 hours a week in the
   year before school. Universal.
2. **Sure Start**: younger children in disadvantaged areas, including a
   programme for 2-year-olds.
3. **Student Finance NI Childcare Grant**.
4. **NI EMA**.

## Implementation outline

For each new programme:

- New parameter tree under `parameters/gov/<region>/<programme>/`
  capturing the income tests, hours offered, and weekly funding rates.
- New variable(s) under `variables/gov/<region>/<programme>/` gated on
  the appropriate `country == ...` check.
- A `<programme>_eligible` companion variable that the new programme
  variable composes with the rate parameter, the same pattern as the
  English entitlement trio.
- A `programs.yaml` row per programme, bound to the new variable and
  parameter prefix.

### Structural items deferred to this work

The [#1644 audit][issue-1644] also flagged two structural items that
become more pressing once the regional programmes land:

- `weeks_per_year` and `childcare_funding_rate` currently sit at
  `gov.dfe.*` root but encode English term-week and funding-rate
  assumptions. They should be regionalised (for example
  `gov.scottish_government.funded_early_learning_childcare.weeks_per_year`)
  once the Scotland, Wales and NI programmes are modelled.
- No aggregating variable across programmes exists (for example "total
  subsidised childcare hours per child per week"). The API surfaces
  the per-programme variables but can't answer "what's this family's
  combined childcare support" without the caller summing.

Both belong in a separate cleanup PR rather than mixed into the
per-programme work.

## Data needs

Most regional programmes are point-in-time per-hour funding rather
than per-household payments, so the data side is comparatively easy:

- **FRS** provides `region` and `country` at the household level,
  enough to gate eligibility.
- **Welsh Government Statistical Bulletins** publish Flying Start
  and Childcare Offer caseloads by local authority.
- **Scottish Government Childcare and Early Years statistics** provide
  Scottish funded ELC caseloads.
- **Department of Education NI** publishes PSEP caseloads.
- The SAAS, Student Finance Wales and NI childcare grants need the same
  treatment as the English `childcare_grant`: calibration against
  published award totals.

The aggregating challenge is choosing whether to expose **subsidised
hours** or **subsidised cost** as the primary household-level
variable. Recommendation: subsidised cost, since that is how the English
entitlements already enter `household_benefits` and `gov_spending`.

## Open questions

- Should the Scottish ELC universal strand and the eligible-two-year-old
  strand be modelled as two separate variables (matching how England
  splits Universal / Extended / Targeted), or as one variable with the
  age-and-eligibility logic inside? Recommendation: separate, mirroring
  the English pattern for queryability.
- Welsh Flying Start is geographic. Microcosm UK assigns each household
  to a 2021 Output Area, which nests in LSOAs, so eligibility by area is
  now possible once the Flying Start area list is sourced.
- EMA ended in England but still runs in Scotland, Wales and Northern
  Ireland. Today `child_ema` and `adult_ema` are reported amounts with
  no formula. Should the devolved schemes be modelled under the existing
  `gov.dfe.care_to_learn` umbrella or as separate regional schemes?

## References

- Audit: [#1644](https://github.com/PolicyEngine/policyengine-uk/issues/1644), the full childcare coverage audit.
- Tracking: [#1008](https://github.com/PolicyEngine/policyengine-uk/issues/1008), the original Scotland, Wales and NI gap report.
- Recent landed work: [#1643][pr-1643], Scottish universal funded ELC.
- Existing England docs (for the pattern to mirror): the entitlement variables under [`policyengine_uk/variables/gov/dfe/`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/dfe).
- Welsh childcare statute: [Childcare Funding (Wales) Act 2019][wales-act].
- Scottish eligible-2-year-old statute: [SSSI 2014/196][sssi-196-2014].

[issue-1644]: https://github.com/PolicyEngine/policyengine-uk/issues/1644
[pr-1643]: https://github.com/PolicyEngine/policyengine-uk/pull/1643
[wales-act]: https://www.legislation.gov.uk/anaw/2019/1/contents
[sssi-196-2014]: https://www.legislation.gov.uk/ssi/2014/196/contents/made
[scot-ema]: https://www.mygov.scot/ema
