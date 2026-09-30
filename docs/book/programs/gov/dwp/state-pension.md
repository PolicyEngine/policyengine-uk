# State Pension

The State Pension is modelled in PolicyEngine UK as three composable
person-level variables, summed into the `state_pension` aggregate that
flows into household benefits. This page describes the current model
and the residual aggregate gap against OBR outturn tracked under
[#1632](https://github.com/PolicyEngine/policyengine-uk/issues/1632).

## Components

Three variables under `gov/dwp/`:

- **`basic_state_pension`** — the pre-2016 flat-rate State Pension paid
  to people who reached State Pension age before 6 April 2016
  (`state_pension_type == BASIC`). Pro-rated by `state_pension_reported`
  against the data-year maximum so partial NI records get the right
  partial rate.
- **`new_state_pension`** — the post-2016 flat-rate State Pension paid
  to people who reached State Pension age on or after 6 April 2016
  (`state_pension_type == NEW`). Same pro-rating logic.
- **`additional_state_pension`** — the earnings-related top-up:
  - For `BASIC` recipients, this is SERPS / S2P (the pre-2016 State
    Earnings-Related / State Second Pension).
  - For `NEW` recipients, this is the **Protected Payment** — pre-2016
    accrual that exceeds the new flat rate, folded into NSP under
    current law but tracked separately in PolicyEngine so the reform
    surface stays clean.
  - Both are computed as `max(reported - flat_max_for_type, 0)` per week,
    multiplied by `WEEKS_IN_YEAR`.

All three split the amount a person reported in the data year (the
dataset's first year) by the person's `state_pension_type` in the year
simulated, and uprate it by that type's flat rate: the year's full rate
over the data year's. Together they pay the reported amount uprated by the
flat rate, for anyone over State Pension age.

Survey ages are held fixed in the years a dataset is projected to, so a
record's birth cohort moves one year later for each year projected, and its
type can change: a man aged 75 in the 2024-25 data reached State Pension age
in 2014, on the basic State Pension, but a man aged 75 in 2030-31 reached it
in 2021, on the new State Pension. Until the fix for
[#1921](https://github.com/PolicyEngine/policyengine-uk/issues/1921),
`additional_state_pension` used the data year's type while the other two
used the year's, so for records like his the part of the reported amount
between the basic and new flat rates was paid twice. The records keep their
reported amounts: a record that moves to a new State Pension cohort is not
given a new State Pension award.

The flag-up split (`state_pension_type`) is settled by [PR #1618](https://github.com/PolicyEngine/policyengine-uk/pull/1618):
classification is based on whether the person reaches State Pension age
before or on/after 6 April 2016. No component is paid before State
Pension age.

## State Pension age

State Pension age depends on date of birth. Pensions Act 1995 Schedule 4
paragraph 1 sets it for each birth period, either as an age or as the day
on which it is attained, and the Pensions Act 2014 s.26 raises it from 66
to 67 for people born on or after 6 April 1960: 66 years and 1 to 11
months for births from 6 April 1960 to 5 March 1961, and 67 from 6 March
1961. The parameters under `gov/dwp/state_pension/age/` encode that
timetable row by row:

- `age_by_birth_date` — the age, in months, by date of birth (women, and
  men born on or after 6 December 1953);
- `day_by_birth_date` — the day, where the statute sets a day instead;
- `male/age` and `male/born_before` — rule (1): men born before 6
  December 1953 attain it at 65.

A person attains State Pension age on the later of the two. The model
places each person's date of birth with `age` and
`months_since_last_birthday`, which counts months since their last
birthday on 6 October, the middle of the fiscal year:

- `state_pension_age` is the person's own State Pension age;
- `months_since_state_pension_age` is how long before 6 October they
  attained it (negative if later);
- `is_SP_age` is whether they have attained it by 6 October, so are over
  it for most of the year.

Simulations of a household situation take a whole age to be the middle of
the year of age (six months since the birthday); a fractional age is read as
the exact age on 6 October. Survey microdata records whole years only, so in
simulations built from data, including a region or constituency filtered
from it, each single year of age and sex is spread evenly over the year by
weight, and `filter_dataset` carries each person's place into a household it
extracts. The weighted share of each age over State Pension age then matches
the statute: three quarters of 66-year-olds in 2026-27, a quarter in 2027-28
and none from 2028-29.

A person attains an age at the start of the anniversary of their birth
(Family Law Reform Act 1969 s.9(1)), and an age of "N years and M months" on
the same day of the month, or the month's last day where that day does not
exist; that also gives the three days rule (7A) sets. A reform can change the
age or day of any row, or where a row starts; a new phase-in that needs extra
rows, such as bringing forward the rise to 68, needs new rows in the
parameter files.

## Uprating

State Pension flat-rate parameters live in
`gov/dwp/state_pension/basic_state_pension/amount.yaml` and
`gov/dwp/state_pension/new_state_pension/amount.yaml`. Both are uprated
under the **triple lock**: the maximum of earnings growth, CPI
inflation, or the 2.5% floor parameterised at
`gov/dwp/state_pension/triple_lock/minimum_rate.yaml`. Active components
of the triple lock are controlled by:

- `triple_lock/active.yaml` — top-level toggle.
- `triple_lock/include_earnings.yaml` — whether the earnings limb is
  active.
- `triple_lock/include_inflation.yaml` — whether the CPI limb is active.

These flags exist so that policy reforms can disable individual limbs
(e.g. "double lock" scenarios that drop the earnings or inflation limb).

## Known aggregate gap (#1632)

The model's State Pension covers UK private households: the Family
Resources Survey covers private households only, not nursing homes and
other communal establishments. The OBR's State Pension line matches DWP's
forecast of State Pension spending, which covers Great Britain and UK State
Pensions paid to people living abroad, but not Northern Ireland, whose
State Pension the Department for Communities pays. The table compares full
microsimulation runs on the enhanced FRS 2024-25
(policyengine-uk-data-private 1.57.4) with that line less DWP's payments
abroad.

| £bn | 2024-25 | 2025-26 | 2026-27 | 2027-28 | 2028-29 | 2029-30 | 2030-31 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Model State Pension | 119.0 | 124.8 | 129.6 | 130.9 | 132.9 | 136.9 | 140.9 |
| OBR March 2026 EFO, State Pension | 138.0 | 146.2 | 154.2 | 158.9 | 164.0 | 172.2 | 180.7 |
| of which paid abroad (DWP) | 5.3 | 5.6 | 5.9 | 6.1 | 6.2 | 6.4 | 6.6 |
| Model minus OBR less paid abroad | -13.6 | -15.8 | -18.6 | -21.9 | -24.8 | -28.9 | -33.2 |

The model also includes Northern Ireland, which the OBR line does not, so
the like-for-like gap is larger by Northern Ireland's State Pension. In
2024-25, the data year, DWP's outturn for residents of Great Britain is
£131.2bn, £12.2bn above the model. The FRS's own grossed estimate for
the UK that year, with benefit amounts linked to DWP records, is £130.6bn,
against £135.1bn from administrative data, so most of the model's shortfall
arises in building the enhanced FRS rather than in the survey's coverage.

The gap widens in later years for two reasons:

- **Caseload.** Survey ages are held fixed in projected years and household
  weights grow with total population
  (`policyengine_uk/data/uprating_indices.yaml`), so the
  pension-age population keeps the data year's age structure. From 2025-26
  to 2030-31 the model's State Pension recipients fall 3.0%, as State
  Pension age rises to 67, while DWP's caseload less those paid abroad rises
  4.8%.
- **Awards.** Each record keeps its reported amount, uprated by the flat
  rate, including records whose cohort moves from basic to new State
  Pension. The model's State Pension per recipient grows 16.4% over those
  years. DWP's spending per recipient, less those paid abroad, grows 18.3%,
  as its new State Pension spending grows from £56.1bn to £102.4bn and its
  basic State Pension spending falls from £66.7bn to £57.8bn.

Until the fix for [#1921](https://github.com/PolicyEngine/policyengine-uk/issues/1921),
`additional_state_pension` paid the band between the flat rates twice for
records moving from basic to new State Pension cohorts (see Components
above): £0.8bn in 2025-26, rising to £6.8bn in 2030-31.
That made the model's State Pension per recipient grow 21.2%, faster than
DWP's, and hid part of the gap.

### What's been fixed

| Issue | Status | Where |
|-------|--------|-------|
| BASIC vs NEW classification used `is_SP_age` heuristic | Fixed | #1618 |
| `new_state_pension` returned flat max for every NEW retiree, ignoring partial NI records | Fixed | #1634 |
| Protected Payment only computed for BASIC-type recipients | Fixed | #1634 (ASP now extends to NEW) |
| `additional_state_pension` split the reported amount by the data year's State Pension type, paying part of it twice for records moving from basic to new cohorts | Fixed | #1921 |

### What's still open

The data year's gap appears to come from the **data side** rather than
the formula. The FRS records State Pension as a single weekly
benefit value (`state_pension_reported`), which is derived from the
DWP-administered single weekly figure (SRP). For BASIC-type retirees
who reported exactly the maximum basic rate, the formula assigns ASP =
0 — but in reality many of those retirees also received SERPS / S2P
top-ups that the single weekly figure either caps or rounds.

The proposed data-side fix lives in `policyengine-uk-data` and would:

- Impute an ASP component on BASIC-type rows whose reported state
  pension matches the max basic rate exactly, using the DWP-published
  share of SERPS / S2P recipients in that band.
- Source the ASP-by-band distribution from ONS *National Pensioners
  Survey* breakdowns or DWP administrative caseload by pension type.

Projected years also need the pension-age population to follow its
cohorts, and records that move to a new State Pension cohort to get that
cohort's awards; neither is modelled.

This is tracked under [#1632](https://github.com/PolicyEngine/policyengine-uk/issues/1632)
and the broader UK pipeline-alignment tracker
[#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621).

## References

- DWP, [New State Pension](https://www.gov.uk/new-state-pension) and [Basic State Pension](https://www.gov.uk/state-pension) user-facing pages.
- HMRC, [State Pension forecast](https://www.gov.uk/check-state-pension) (the underlying SP1 figure that lands in the FRS).
- [Pensions Act 2014](https://www.legislation.gov.uk/ukpga/2014/19/contents) — introduces the New State Pension and the BASIC / NEW boundary.
- [Social Security Contributions and Benefits Act 1992, Part 2](https://www.legislation.gov.uk/ukpga/1992/4/part/II) — primary statute for the basic scheme.
- OBR, [Economic and fiscal outlook, March 2026: detailed forecast tables, expenditure](https://obr.uk/download/march-2026-economic-and-fiscal-outlook-detailed-forecast-tables-expenditure/), table 4.9, "State pension".
- DWP, [Benefit expenditure and caseload tables 2026: outturn and forecast, Spring Forecast 2026](https://assets.publishing.service.gov.uk/media/69dcdc8c6b695d635c34dcc4/outturn-and-forecast-tables-spring-forecast-2026.xlsx), "State Pension" sheet: total, paid outside the UK, components and caseload.
- DWP, [State Pension expenditure by country of residence, 2024-25](https://assets.publishing.service.gov.uk/media/693ffff9cfacd5e888491fb6/State-Pension-by-country-2024-25.ods), for the 2024-25 outturn for residents of Great Britain.
- DWP, [Family Resources Survey, integrating administrative data for benefits: tables](https://assets.publishing.service.gov.uk/media/69c416acb66ff902f45441f0/family-resources-survey-transformation-benefits.xlsx), sheet 16, State Pension: admin-linked survey and administrative estimates, 2024-25.
- DWP, [Family Resources Survey 2024-25: background information and methodology](https://www.gov.uk/government/statistics/family-resources-survey-financial-year-2024-to-2025/family-resources-survey-background-information-and-methodology), section 4.1, for the survey's coverage of private households.
- House of Commons Library, [State Pension triple lock](https://commonslibrary.parliament.uk/research-briefings/cbp-7812/) — context for the triple-lock parameters.
