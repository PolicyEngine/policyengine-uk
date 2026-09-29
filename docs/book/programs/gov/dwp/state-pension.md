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
before or on/after 6 April 2016.

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
forecast of the statutory measure minus its calendar-year forecast, from the
same Economic and Fiscal Outlook:

- September CPI: the OBR's September CPI forecast (receipts Table 3.19, the
  CPI used to uprate tax thresholds), or Q3 CPI (economy Table 1.7) in years
  that table does not cover;
- May-July earnings: Q2 average earnings growth (economy Table 1.6). The
  OBR does not forecast the ONS AWE series; its measure is wages and
  salaries per employee, and Q2 is the quarter nearest May to July.

After the EFO horizon the gap is zero, so the inputs follow calendar-year
growth. `policyengine_uk/utils/import_obr_forecasts.py` regenerates the gaps
with the calendar-year series (pass `--receipts-file` or `--receipts-url`
for September CPI).

### Scenarios

A macro scenario applied before the data load that edits calendar-year
growth moves the forecast inputs one for one, and so the triple lock:

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

These changes must go through `Scenario(parameter_changes=...)`. The rates
are built when parameters are processed, and a `reform=` dictionary edits
parameters after that, so it changes the parameter but not the uprating.

### Reform levers

- `triple_lock/active.yaml` switches the triple lock off. The pension then
  rises by the statutory minimum from the review under the Social Security
  Administration Act 1992, section 150A: earnings growth, and nothing when
  earnings fall.
- `triple_lock/include_earnings.yaml` and
  `triple_lock/include_inflation.yaml` drop an element, e.g. for a double
  lock.
- `triple_lock/minimum_rate.yaml` sets the floor.
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
