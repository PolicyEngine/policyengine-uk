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

The current childcare coverage is recorded in
[`policyengine_uk/programs.yaml`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/programs.yaml),
where [#1703](https://github.com/PolicyEngine/policyengine-uk/pull/1703)
split the old umbrella entry into per-programme rows after the
[#1644 audit][issue-1644]. Care to Learn and the Scottish funded ELC have
no row yet. Coverage works as follows:

- **UK-wide**: Tax-Free Childcare (HMRC); Universal Credit childcare
  element (DWP); Working Tax Credit childcare element (legacy, HMRC
  administered, ended 5 April 2025, modelled under `gov/dwp/`; see
  [tax-credits.md](./../dwp/tax-credits.md)).
- **England-only** (gate on `country == ENGLAND`):
  Universal Childcare Entitlement (15 hours for 3- and 4-year-olds),
  Extended Childcare Entitlement (working parents, now reaching down to
  children aged nine months), Targeted Childcare Entitlement (2-year-olds
  in families on qualifying benefits, or on Universal Credit or tax
  credits with income below a limit), Care to Learn, Student Finance
  England Childcare Grant.
- **Scotland**: eligibility for the universal funded ELC for 3- and
  4-year-olds (`scottish_funded_early_learning_childcare_eligible`, with
  the statutory start date for 3-year-olds taken as an input,
  `scottish_funded_early_learning_childcare_start_date_reached`) and its
  1,140 hours a year, added in [#1643][pr-1643]. No funding value is
  attached yet, so it does not reach household income.
- **Wales, Northern Ireland**: no programmes modelled.

## Proposed scope by jurisdiction

### Scotland: three remaining strands

The [#1644 audit][issue-1644] flagged three Scottish gaps:

1. **Eligible-two-year-old strand** of the funded ELC programme:
   2-year-olds who are looked after, under a kinship care order or with
   an appointed guardian ([Children and Young People (Scotland) Act 2014
   s. 47(3)][cyp-47]), or whose parent receives a qualifying benefit
   under the [Provision of Early Learning and Childcare (Specified
   Children) (Scotland) Order 2014][ssi-196-2014]. It would be modelled
   the same way as the 3- and 4-year-old strand but gated on those
   conditions. The qualifying benefits include Universal Credit with
   earned income of up to £850 an assessment period; Child Tax Credit
   was removed from the list from 6 April 2025 ([SSI 2025/82][ssi-82-2025]).
2. **Student Awards Agency Scotland (SAAS) support for student
   parents**: the Childcare Funds that universities and colleges pay out
   (a Lone Parents' Childcare Grant of up to £1,215 a year, not
   income-assessed, plus discretionary help assessed on need), the
   closest Scottish equivalent of Student Finance England's Childcare
   Grant ([SAAS childcare fund guidance, 2026 to 2027][saas-childcare]);
   and SAAS's income-assessed Lone Parents' Grant (up to £1,305). The
   audit also listed SAAS's Dependants' Grant, but that supports adult
   dependants rather than children.
3. **Support for young parents in further education**, the role Care to
   Learn plays in England. The [Education Maintenance Allowance][scot-ema]
   still runs in Scotland for 16- to 19-year-olds, applied for through
   local councils and colleges, but it is a maintenance payment rather
   than childcare support, so the childcare side needs its own scoping.

### Wales

The audit identified four Welsh programmes:

1. **Childcare Offer for Wales**: up to 30 hours a week of combined
   nursery education (at least 10 hours) and childcare, for up to 48
   weeks a year, for 3- and 4-year-olds of working parents or parents in
   further or higher education
   ([gov.wales](https://www.gov.wales/get-30-hours-childcare-3-and-4-year-olds)).
   Modelled the same as the English Extended Childcare Entitlement
   with Welsh-specific income tests and hour caps. Statutory basis:
   [Childcare Funding (Wales) Act 2019][wales-act].
2. **Flying Start**: funded childcare for 2- to 3-year-olds in some of
   the most disadvantaged areas of Wales (12.5 hours a week, 39 weeks a
   year), expanded in phases since 2022 with the aim of reaching all
   2-year-olds
   ([Welsh Government guidance](https://www.gov.wales/flying-start-childcare-guidance-html)).
   Eligibility is geographic, based on lower layer super output areas
   chosen by each local authority.
3. **Student Finance Wales Childcare Grant**, parallel to the English
   Childcare Grant.
4. **Welsh EMA**, parallel to the Scottish EMA.

### Northern Ireland

The audit identified four NI programmes:

1. **Pre-school Education Programme (PSEP)**: a funded place in the
   immediate pre-school year for every child whose family wants one.
   In December 2024, 60% of children had 12.5 hours a week and 40% had
   22.5 hours; the Department of Education is moving places to 22.5
   hours, starting with 77 settings from September 2025
   ([Department of Education](https://www.education-ni.gov.uk/news/education-minister-announces-first-step-major-expansion-pre-school-education-provision)).
2. **Sure Start**: younger children in disadvantaged areas, including a
   programme for 2-year-olds.
3. **Student Finance NI Childcare Grant**.
4. **NI EMA**.

## Implementation outline

For each new programme:

- New parameter tree under the administering body (as #1643 did with
  `parameters/gov/scottish_government/<programme>/`) capturing the
  income tests, hours offered, and weekly funding rates.
- New variable(s) under the matching `variables/gov/<body>/<programme>/`
  folder, gated on the appropriate `country == ...` check.
- A `<programme>_eligible` companion variable that the new programme
  variable composes with the rate parameter, the same pattern as the
  English entitlement trio.
- A `programs.yaml` row per programme, bound to the new variable and
  parameter prefix.

### Structural items deferred to this work

The [#1644 audit][issue-1644] also listed four structural findings.
#1703 has since split the `programs.yaml` umbrella row, and one (a
shared `in_england` helper) is minor; the other two become more pressing
once the regional programmes land:

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

Several regional programmes (the Scottish two-year-old strand, the
Childcare Offer, Flying Start and PSEP) are funded hours rather than
cash payments, so their data side is comparatively easy:

- **FRS** provides the household's `region`, from which the model
  derives `country`; that is enough to gate eligibility.
- **Welsh Government** publishes Flying Start official statistics with
  local authority breakdowns, and an annual Childcare Offer for Wales
  report that gives the number of children using the Offer by local
  authority.
- **Scottish Government Funded Early Learning and Childcare Statistics**
  (the annual ELC census) provide funded ELC registrations, including
  eligible two-year-olds.
- **Department of Education NI** publishes PSEP caseloads.
- The SAAS, Student Finance Wales and Student Finance NI childcare
  grants need published award totals to check the modelled amounts
  against. The English `childcare_grant` has no calibration target yet:
  the Student Loans Company targets in policyengine-uk-data cover
  Parents' Learning Allowance and Adult Dependants' Grant only.

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
- Welsh Flying Start is geographic. Microcosm UK, the default UK dataset
  in the policyengine.py bundle since release 6.10.0 (21 October 2026),
  places each household in its local-area build in one atomic area
  (a 2021 Output Area in England and Wales, a 2022 Output Area in
  Scotland, a 2021 Data Zone in Northern Ireland) and derives larger
  geographies such as LSOAs from it. The national file carries no small
  areas. Eligibility by area becomes possible on the local-area build
  once the Flying Start LSOA list is sourced.
- EMA ended in England but still runs in Scotland, Wales and Northern
  Ireland. Today `child_ema` and `adult_ema` (under
  `variables/gov/dwp/`) are reported FRS amounts with no formula. Should
  the devolved schemes sit alongside the England-only
  `gov.dfe.care_to_learn` tree, or be separate schemes under each
  administration?

## References

- Audit: [#1644](https://github.com/PolicyEngine/policyengine-uk/issues/1644), the full childcare coverage audit.
- Tracking: [#1008](https://github.com/PolicyEngine/policyengine-uk/issues/1008), the original Scotland, Wales and NI gap report.
- Recent landed work: [#1643][pr-1643], Scottish universal funded ELC; [#1703](https://github.com/PolicyEngine/policyengine-uk/pull/1703), per-programme `programs.yaml` rows.
- Existing England implementation (the pattern to mirror): the entitlement variables under [`policyengine_uk/variables/gov/dfe/`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/dfe).
- Welsh childcare statute: [Childcare Funding (Wales) Act 2019][wales-act].
- Scottish eligible-2-year-old legislation: [Children and Young People (Scotland) Act 2014 s. 47(3)][cyp-47] and [SSI 2014/196][ssi-196-2014], as amended by [SSI 2025/82][ssi-82-2025].
- SAAS, [University Childcare Fund guidance, 2026 to 2027][saas-childcare].

[issue-1644]: https://github.com/PolicyEngine/policyengine-uk/issues/1644
[pr-1643]: https://github.com/PolicyEngine/policyengine-uk/pull/1643
[wales-act]: https://www.legislation.gov.uk/anaw/2019/1/contents
[ssi-196-2014]: https://www.legislation.gov.uk/ssi/2014/196/contents
[ssi-82-2025]: https://www.legislation.gov.uk/ssi/2025/82/made
[cyp-47]: https://www.legislation.gov.uk/asp/2014/8/section/47
[saas-childcare]: https://www.saas.gov.uk/files/311/saas-childcare-fund-guidance.pdf
[scot-ema]: https://www.mygov.scot/ema
