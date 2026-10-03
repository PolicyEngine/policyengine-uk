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
simulated. The part up to that type's full rate in the data year is basic
or new State Pension, and the part above it is additional State Pension.
Both parts are uprated by the type's full rate (the year's over the data
year's), so together they pay the reported amount uprated by the flat rate,
for anyone over State Pension age. In law, additional pensions and
protected payments rise with prices instead: the Social Security Benefits
Up-rating Order 2026 raised them by 3.8% in April 2026 (articles 4(3) and
6(3)), and the full rates by 4.8%. This is tracked in
[#1941](https://github.com/PolicyEngine/policyengine-uk/issues/1941).

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
given a new State Pension award. That is one reason the model's State
Pension per recipient grows more slowly than DWP's (see Known aggregate gap
below).

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
the exact age on 6 October, overriding `months_since_last_birthday` even
when another person supplies birthday months. The default implies a birth
date of 6 April: an entered age of 66 is above State Pension age at the
6 October check in 2026-27 and below it in 2027-28. Set a fractional age
or `months_since_last_birthday` to specify a different inferred birth date.
Survey microdata records whole years only, so in
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

The removed scalar parameters `gov.dwp.state_pension.age.male` and `.female`
remain discoverable in metadata as migration nodes: explicit root `get_child`
lookups, updates, and scalar value-history reads for saved API policies raise
an error naming the birth-date
scales above. The `male.age` and `male.born_before` children remain available
for the earlier male cohorts. For example, reform
`gov.dwp.state_pension.age.age_by_birth_date[14].amount` to change the age
in months for births from 6 March 1961 until the next bracket; read individual
eligibility from `is_SP_age` or the individual threshold from `state_pension_age`.

## Uprating

State Pension flat-rate parameters live in
`gov/dwp/state_pension/basic_state_pension/amount.yaml` and
`gov/dwp/state_pension/new_state_pension/amount.yaml`. Published rates run
to 2026-27; later years are uprated by
`gov.economic_assumptions.indices.triple_lock`, built from the yearly rates
in `gov.economic_assumptions.yoy_growth.triple_lock`.

### The triple lock

The rise each April is the highest of:

- **earnings growth**: average weekly earnings, total pay, whole economy, in
  May to July of the previous year on a year earlier (ONS KAC3);
- **CPI inflation**: the 12-month rate in September of the previous year
  (ONS D7G7);
- **2.5%**: `triple_lock/minimum_rate.yaml`.

`create_triple_lock.py` computes each element from these statutory inputs,
rounded to the one decimal place the ONS publishes. From them it reproduces
every published rise from April 2012 to April 2026. April 2011 is the one
override (`triple_lock/outturn.yaml`): the basic State Pension rose by
September 2010 RPI (4.6%) during the switch to CPI. The April 2022
suspension of the earnings element is `include_earnings` set to false for
that year.

The yearly rates run from April 2011 to one year past the end of the
economic-assumption series.

### The statutory inputs

`gov.economic_assumptions.statutory_uprating_inputs` holds:

- `cpi_september`: September CPI, keyed to 1 September;
- `awe_total_pay_may_july`: May-July earnings growth, keyed to 1 July, as
  used in the uprating review.

Each holds published figures and then a null. From the null onwards,
`create_statutory_uprating_inputs.py` fills in a forecast: calendar-year
growth in the matching OBR series (`yoy_growth.obr.consumer_price_index` or
`yoy_growth.obr.average_earnings`) plus `forecast_gap`. The gap is the OBR's
statutory-basis forecast minus the calendar-year growth stored in
`yoy_growth.yaml`, so that in the baseline the input equals the OBR's figure:

- September CPI: the OBR's September CPI forecast (receipts Table 3.19, the
  CPI used to uprate tax thresholds), or Q3 CPI (economy Table 1.7) in years
  that table does not cover;
- May-July earnings: Q2 average earnings growth (economy Table 1.6). The
  OBR does not forecast the ONS AWE series; its measure is wages and
  salaries per employee, and Q2 is the quarter nearest May to July.

After the EFO horizon the gap is zero, so the inputs follow calendar-year
growth. Smooth forecasts pay the higher of earnings, CPI and 2.5% each year,
so the baseline has none of the extra cost the triple lock builds up when
September CPI and May-July earnings take turns to spike; the OBR's long-run
projections add 0.56 percentage points a year over earnings for it (Fiscal
risks and sustainability, July 2026). To capture it, supply simulated paths
of the statutory inputs, as below.

`policyengine_uk/utils/import_obr_forecasts.py` regenerates the gaps with the
calendar-year series, from the EFO economy and receipts tables
(`--receipts-file` or `--receipts-url`). After editing `yoy_growth.yaml` by
hand, run it with `--gaps-only`.

### Scenarios

A macro scenario applied before the data load that edits calendar-year
growth moves the forecast inputs one for one, and so the triple lock.
Calendar-year series are keyed to 1 January, so key the change
`year:YYYY-01-01:1`: a bare year names the fiscal year from 6 April, which
lands in the next calendar-year value and so moves the following year's
inputs.

```python
from policyengine_uk.model_api import Scenario

scenario = Scenario(
    parameter_changes={
        "gov.economic_assumptions.yoy_growth.obr.average_earnings": {
            "year:2027-01-01:1": 0.05,
        },
    },
    applied_before_data_load=True,
)
```

A scenario can also set the statutory inputs directly, for example from a
model of the monthly series, since the triple lock pays out on how September
CPI and May-July earnings differ from each other. A value replaces the
forecast for that year only; a bare year names the fiscal year from 6 April,
which contains both observation dates:

```python
Scenario(
    parameter_changes={
        "gov.economic_assumptions.statutory_uprating_inputs.cpi_september": {
            "2027": 0.031,
        },
        "gov.economic_assumptions.statutory_uprating_inputs.awe_total_pay_may_july": {
            "2027": 0.024,
        },
    },
    applied_before_data_load=True,
)
```

These changes, and the reform levers below, must go through
`Scenario(parameter_changes=...)`. The rates are built when parameters are
processed, and a `reform=` dictionary edits parameters after that, so it
changes the parameter but not the uprating.

### Reform levers

- `triple_lock/minimum_rate.yaml` sets the floor. A double lock, the higher
  of earnings and CPI, is the floor set to 0 (or below 0 to allow cash
  cuts).
- `triple_lock/include_earnings.yaml` and
  `triple_lock/include_inflation.yaml` drop an element but keep the floor.
  A CPI link is `include_earnings` false with the floor at or below 0.
- `triple_lock/active.yaml` switches the triple lock off. The pension then
  rises by the statutory minimum from the review under the Social Security
  Administration Act 1992, section 150A: earnings growth, and nothing when
  earnings fall. The floor and the include flags no longer apply, and
  neither do the one-year changes to section 150A for April 2021 and April
  2022.
- `triple_lock/earnings_path_guarantee.yaml` (off under current law) keeps
  the pension on or above an earnings path started from its level in the
  year before the guarantee first applies. With `include_earnings` false,
  it models a plan that drops the earnings element of the triple lock but
  keeps the pension in line with earnings over time. The plan announced on
  29 September 2026 gave no formula; one reading, from April 2030, is:

```python
Scenario(
    parameter_changes={
        "gov.dwp.state_pension.triple_lock.include_earnings": {
            "year:2030-01-01:100": False,
        },
        "gov.dwp.state_pension.triple_lock.earnings_path_guarantee": {
            "year:2030-01-01:100": True,
        },
    },
    applied_before_data_load=True,
)
```

Each guaranteed year, the rise is the highest of the triple lock elements
still included and the rise needed to reach the earnings path, rounded up to
0.1 percentage points.

## Known aggregate gap (#1632)

The model's State Pension covers UK private households: the Family
Resources Survey covers private households only, not nursing homes and
other communal establishments. DWP's State Pension spending covers Great
Britain and UK State Pensions paid to people living abroad, but not
Northern Ireland, whose State Pension the Department for Communities pays.
DWP's Spring Forecast 2026 is consistent with the OBR's March 2026 forecast.
From 2026-27 the two differ by about £2m a year. The OBR's figures are
£1.4bn higher in 2024-25, which the OBR records as outturn, and £0.1bn
higher in 2025-26.

The table compares full microsimulation runs on the enhanced FRS 2024-25
(policyengine-uk-data-private 1.57.4) with DWP's spending less its payments
abroad.

| £bn | 2024-25 | 2025-26 | 2026-27 | 2027-28 | 2028-29 | 2029-30 | 2030-31 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Model State Pension | 119.0 | 124.8 | 129.6 | 130.9 | 132.9 | 136.9 | 140.9 |
| OBR March 2026 EFO, State Pension | 138.0 | 146.2 | 154.2 | 158.9 | 164.0 | 172.2 | 180.7 |
| DWP Spring Forecast 2026, State Pension | 136.6 | 146.1 | 154.2 | 158.9 | 164.0 | 172.2 | 180.7 |
| of which paid abroad | 5.3 | 5.6 | 5.9 | 6.1 | 6.2 | 6.4 | 6.6 |
| Model minus DWP less paid abroad | -12.2 | -15.6 | -18.6 | -21.9 | -24.8 | -28.9 | -33.1 |

The model also includes Northern Ireland, which DWP's figures do not, so the
like-for-like gap is larger by Northern Ireland's State Pension.

**The data year.** In 2024-25 the model has 11.36m State Pension recipients
averaging £201.6 a week. The FRS's own grossed figures are 11.53m recipients
averaging £212 a week, and DWP's administrative figures are 11.88m and £212
(FRS methodology tables M.6a and M.6b). The FRS's grossed estimate for the
UK, with benefit amounts linked to DWP records, is £130.6bn, against
£135.1bn from administrative data. So most of the model's £16bn shortfall
against administrative data for the UK arises in building the enhanced FRS,
not in the survey. For FRS respondents, `state_pension_reported` is the
FRS benefits table's weekly State Pension amount times 52
(policyengine-uk-data's `datasets/frs.py`). On the rows the enhanced FRS
adds from the Survey of Personal Incomes, it is imputed
(`datasets/imputations/frs_only.py`). The shortfall is tracked in
[policyengine-uk-data#493](https://github.com/PolicyEngine/policyengine-uk-data/issues/493).

**Projected years.** The gap widens after the data year for two reasons,
tracked in [#1929](https://github.com/PolicyEngine/policyengine-uk/issues/1929):

- **Caseload.** Survey ages are held fixed in projected years and household
  weights grow with total population
  (`policyengine_uk/data/uprating_indices.yaml`), so the pension-age
  population keeps the data year's age structure. From 2025-26 to 2030-31
  the model's State Pension recipients fall 3.0%, as State Pension age rises
  to 67, while DWP's caseload less those paid abroad rises 4.8%.
- **Awards.** Each record keeps its reported amount, uprated by the flat
  rate, including records whose cohort moves from basic to new State
  Pension. The model's State Pension per recipient grows 16.4% over those
  years. DWP's spending per recipient, less those paid abroad, grows 18.3%,
  as its new State Pension spending grows from £56.1bn to £102.4bn and its
  basic State Pension spending falls from £66.7bn to £57.8bn.

Until the fix for [#1921](https://github.com/PolicyEngine/policyengine-uk/issues/1921),
`additional_state_pension` paid the band between the flat rates twice for
records moving from basic to new State Pension cohorts (see Components
above): £0.8bn in 2025-26, rising to £6.8bn in 2030-31. That made the
model's State Pension per recipient grow 21.2%, faster than DWP's, and hid
part of the widening.

### What's been fixed

| Issue | Status | Where |
|-------|--------|-------|
| BASIC vs NEW classification used `is_SP_age` heuristic | Fixed | #1618 |
| `new_state_pension` returned flat max for every NEW retiree, ignoring partial NI records | Fixed | #1634 |
| Protected Payment only computed for BASIC-type recipients | Fixed | #1634 (ASP now extends to NEW) |
| `additional_state_pension` split the reported amount by the data year's State Pension type, paying part of it twice for records moving from basic to new cohorts | Fixed | #1921 |

### What's still open

- The data year's shortfall in the enhanced FRS:
  [policyengine-uk-data#493](https://github.com/PolicyEngine/policyengine-uk-data/issues/493).
- The pension-age population and new-cohort awards in projected years:
  [#1929](https://github.com/PolicyEngine/policyengine-uk/issues/1929).

Both are part of [#1632](https://github.com/PolicyEngine/policyengine-uk/issues/1632)
and the broader UK pipeline-alignment tracker
[#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621).

## References

- DWP, [New State Pension](https://www.gov.uk/new-state-pension) and [Basic State Pension](https://www.gov.uk/state-pension) user-facing pages.
- GOV.UK, [Check your State Pension forecast](https://www.gov.uk/check-state-pension).
- [Pensions Act 2014](https://www.legislation.gov.uk/ukpga/2014/19/contents) — introduces the New State Pension and the BASIC / NEW boundary.
- [Social Security Contributions and Benefits Act 1992, Part 2](https://www.legislation.gov.uk/ukpga/1992/4/part/II) — primary statute for the basic scheme.
- OBR, [Economic and fiscal outlook, March 2026: detailed forecast tables, expenditure](https://obr.uk/download/march-2026-economic-and-fiscal-outlook-detailed-forecast-tables-expenditure/), table 4.9, "State pension".
- DWP, [Benefit expenditure and caseload tables 2026: outturn and forecast, Spring Forecast 2026](https://assets.publishing.service.gov.uk/media/69dcdc8c6b695d635c34dcc4/outturn-and-forecast-tables-spring-forecast-2026.xlsx), "State Pension" sheet: total, paid outside the UK, components and caseload.
- DWP, [Family Resources Survey, integrating administrative data for benefits: tables](https://assets.publishing.service.gov.uk/media/69c416acb66ff902f45441f0/family-resources-survey-transformation-benefits.xlsx), sheet 16, State Pension: admin-linked survey and administrative estimates, 2024-25.
- DWP, [Family Resources Survey 2024-25: methodology and standard error tables](https://assets.publishing.service.gov.uk/media/69c3c0d2471d520038d0f571/ch1_methodology_and_standard_errors.xlsx), tables M.6a and M.6b: State Pension recipients and weekly amounts, FRS against administrative data.
- DWP, [Family Resources Survey 2024-25: background information and methodology](https://www.gov.uk/government/statistics/family-resources-survey-financial-year-2024-to-2025/family-resources-survey-background-information-and-methodology), section 4.1, for the survey's coverage of private households.
- House of Commons Library, [State Pension triple lock](https://commonslibrary.parliament.uk/research-briefings/cbp-7812/) — context for the triple-lock parameters.
