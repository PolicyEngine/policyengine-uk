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
and the broader [#1644 audit](./../../../programs.yaml).
```

## What's modelled today

The current childcare coverage is captured in `programs.yaml` (see the
[#1644 split into per-programme rows][issue-1644]) and works as follows:

- **UK-wide**: Tax-Free Childcare (HMRC); Universal Credit childcare
  element (DWP); Working Tax Credit childcare element (DWP, legacy, see
  [tax-credits.md](./../dwp/tax-credits.md)).
- **England-only** (gate on `country == ENGLAND`):
  Universal Childcare Entitlement (15h), Extended Childcare Entitlement
  (30h working parents), Targeted Childcare Entitlement (disadvantaged
  2-year-olds + working families with younger children), Care to Learn,
  Student Finance England Childcare Grant.
- **Scotland**: Universal Funded ELC for 3- and 4-year-olds (1,140
  hrs/year) added in [#1643][pr-1643].
- **Wales, Northern Ireland**: no programmes modelled.

## Proposed scope by jurisdiction

### Scotland — three remaining strands

The [#1644 audit][issue-1644] flagged three Scottish gaps:

1. **Eligible-two-year-old strand** of the funded ELC programme
   (vulnerable / low-income 2-year-olds under the
   [Provision of Early Learning and Childcare (Specified Children)
   (Scotland) Order 2014][sssi-196-2014]). Modelled the same way as the
   3- and 4-year-old strand but gated on a means test against UC /
   tax credits / equivalent qualifying benefits.
2. **Student Awards Agency Scotland (SAAS) Lone Parents' Grant,
   Dependants' Grant, and Childcare Fund** for full-time HE students
   — the Scottish equivalent of Student Finance England's Childcare
   Grant. Income-tested, paid at standard weekly rates.
3. **Scottish EMA-equivalent** for young parents in further education
   (the [Educational Maintenance Allowance][saas-ema] is paid by local
   authorities in Scotland under SAAS oversight; the childcare-support
   layer parallels Care to Learn in England).

### Wales

The audit identified four Welsh programmes:

1. **Childcare Offer for Wales** — 30 hours/week for working parents
   of 3- and 4-year-olds (term-time + a portion of holiday weeks).
   Modelled the same as the English Extended Childcare Entitlement
   with Welsh-specific income tests and hour caps. Statutory basis:
   [Childcare Funding (Wales) Act 2019][wales-act].
2. **Flying Start** — universal preschool offer in disadvantaged areas
   for 2- and 3-year-olds (12.5 hours/week). Geographic eligibility
   based on lower-super-output-area data.
3. **Student Finance Wales Childcare Grant** — parallel to the English
   Childcare Grant.
4. **Welsh EMA** — parallel to Scottish EMA.

### Northern Ireland

The audit identified four NI programmes:

1. **Pre-school Education Programme (PSEP)** — 12.5 hours/week for 3-
   and 4-year-olds. Universal.
2. **Sure Start** — younger disadvantaged children (2-3yo).
3. **Student Finance NI Childcare Grant**.
4. **NI EMA**.

## Implementation outline

For each new programme:

- New parameter tree under `parameters/gov/<region>/<programme>/`
  capturing the income tests, hours offered, and weekly funding rates.
- New variable(s) under `variables/gov/<region>/<programme>/` gated on
  the appropriate `country == ...` check.
- A `<programme>_eligible` companion variable that the new programme
  variable composes with the rate parameter — same pattern as the
  English entitlement trio.
- A `programs.yaml` row per programme, bound to the new variable and
  parameter prefix.

### Structural items deferred to this work

The [#1644 audit][issue-1644] also flagged two structural items that
become more pressing once the regional programmes land:

- `weeks_per_year` and `childcare_funding_rate` currently sit at
  `gov.dfe.*` root but encode English term-week and funding-rate
  assumptions. They should be regionalised (e.g.
  `gov.scotland.elc.weeks_per_year`) once the Scotland / Wales / NI
  programmes are modelled.
- No aggregating variable across programmes exists (e.g. "total
  subsidised childcare hours per child per week"). The API surfaces
  the per-programme variables but can't answer "what's this family's
  combined childcare support" without the caller summing.

Both belong in a separate cleanup PR rather than mixed into the
per-programme work.

## Data needs

Most regional programmes are point-in-time per-hour funding rather
than per-household payments, so the data side is comparatively easy:

- **FRS** provides `region` and `country` at the household level —
  enough to gate eligibility.
- **Welsh Government Statistical Bulletins** publish Flying Start
  and Childcare Offer caseloads by local authority.
- **Scottish Government Childcare and Early Years statistics** provide
  Scottish funded ELC caseloads.
- **Department of Education NI** publishes PSEP caseloads.
- The SAAS / Student Finance Wales / NI Childcare Grants need the same
  treatment as the English `childcare_grant` — calibration against
  published award totals.

The aggregating challenge is choosing whether to expose **subsidised
hours** or **subsidised cost** as the primary household-level
variable. Recommendation: subsidised cost, since that's what flows
through to `household_market_income` and the UC childcare element
disregards.

## Open questions

- Should the Scottish ELC universal strand and the eligible-two-year-old
  strand be modelled as two separate variables (matching how England
  splits Universal / Extended / Targeted), or as one variable with the
  age-and-eligibility logic inside? Recommendation: separate, mirroring
  the English pattern for queryability.
- Welsh Flying Start is geographic. Do we have a postcode-to-LSOA
  cross-walk in the FRS pipeline?
- All four EMA / EMA-equivalent schemes are now extinct in England but
  still operational in the devolved nations. Should they be modelled
  under the existing `gov.dfe.care_to_learn` umbrella or as separate
  regional schemes?

## References

- Audit: [#1644](https://github.com/PolicyEngine/policyengine-uk/issues/1644) — full childcare coverage audit.
- Tracking: [#1008](https://github.com/PolicyEngine/policyengine-uk/issues/1008) — original Scotland/Wales/NI gap report.
- Recent landed work: [#1643][pr-1643] — Scottish Universal Funded ELC.
- Existing England docs (for the pattern to mirror): the entitlement variables under [`policyengine_uk/variables/gov/dfe/`](../../../../policyengine_uk/variables/gov/dfe).
- Welsh childcare statute: [Childcare Funding (Wales) Act 2019][wales-act].
- Scottish eligible-2-year-old statute: [SSSI 2014/196][sssi-196-2014].

[issue-1644]: https://github.com/PolicyEngine/policyengine-uk/issues/1644
[pr-1643]: https://github.com/PolicyEngine/policyengine-uk/pull/1643
[wales-act]: https://www.legislation.gov.uk/anaw/2019/1/contents
[sssi-196-2014]: https://www.legislation.gov.uk/ssi/2014/196/contents/made
[saas-ema]: https://www.saas.gov.uk/funding/maintenance-allowance
