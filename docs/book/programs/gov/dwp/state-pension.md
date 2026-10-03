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

Other programmes test State Pension age in two ways:

- **The qualifying age for State Pension Credit** (State Pension Credit Act
  2002 s.1(6)) is a woman's State Pension age, and for a man the State
  Pension age of a woman born on the same day. `state_pension_credit_qualifying_age`
  applies the timetable without rule (1), and
  `has_attained_state_pension_credit_qualifying_age` is whether it is reached
  by 6 October. Pension Credit, Universal Credit (Welfare Reform Act 2012
  s.4(1)(b)), Housing Benefit (Housing Benefit Regulations 2006 reg 5 in both
  sets), Council Tax Reduction's pension-age schemes, Income Support
  (SSCBA 1992 s.124(1)(aa)), the benefit cap (which reaches only
  working-age Housing Benefit and Universal Credit) and Winter Fuel Payment
  (to September 2024) use it. It differs from
  `is_SP_age` only for men born before 6 December 1953, so only in 2018-19
  and earlier: a man born on 6 April 1952 reached it on 6 May 2014, nearly
  three years before his State Pension age of 65.
- **Class 4 National Insurance** stops from the first tax year that begins on
  or after the day State Pension age is reached: a person over it at the
  beginning of the tax year (6 April) is excepted (Social Security
  (Contributions) Regulations 2001 reg 91(a)), so `ni_class_4_liable` needs
  `months_since_state_pension_age` below 6. Someone who reaches it on 6 April
  itself is read as over it at the beginning of that year. Class 1 employee
  contributions stop at State Pension age itself (SSCBA 1992 s.6(3)), which
  the annual model reads as `is_SP_age`.

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

After the BASIC/NEW classification fix in PR #1618 and the pro-rating
+ Protected Payment fixes in [PR #1634](https://github.com/PolicyEngine/policyengine-uk/pull/1634),
the model's State Pension aggregate is **~£127.5 bn** against the OBR
2025 target of **~£140 bn** — a **-£12 bn gap**.

### What's been fixed

| Issue | Status | Where |
|-------|--------|-------|
| BASIC vs NEW classification used `is_SP_age` heuristic | Fixed | #1618 |
| `new_state_pension` returned flat max for every NEW retiree, ignoring partial NI records | Fixed | #1634 |
| Protected Payment only computed for BASIC-type recipients | Fixed | #1634 (ASP now extends to NEW) |

### What's still open

The remaining ~£12 bn gap appears to come from the **data side** rather
than the formula. The FRS records State Pension as a single weekly
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

This is tracked under [#1632](https://github.com/PolicyEngine/policyengine-uk/issues/1632)
and the broader UK pipeline-alignment tracker
[#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621).

## References

- DWP, [New State Pension](https://www.gov.uk/new-state-pension) and [Basic State Pension](https://www.gov.uk/state-pension) user-facing pages.
- HMRC, [State Pension forecast](https://www.gov.uk/check-state-pension) (the underlying SP1 figure that lands in the FRS).
- [Pensions Act 2014](https://www.legislation.gov.uk/ukpga/2014/19/contents) — introduces the New State Pension and the BASIC / NEW boundary.
- [Social Security Contributions and Benefits Act 1992, Part 2](https://www.legislation.gov.uk/ukpga/1992/4/part/II) — primary statute for the basic scheme.
- OBR March 2026 EFO — State Pension expenditure target.
- House of Commons Library, [State Pension triple lock](https://commonslibrary.parliament.uk/research-briefings/cbp-7812/) — context for the triple-lock parameters.
