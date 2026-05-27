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
