# Household-impact tests returning 0 (resolved)

```{note}
**Resolved.** [#1628](https://github.com/PolicyEngine/policyengine-uk/issues/1628)
reported that two `policyengine.py` household-impact integration tests,
which assert that income tax and child benefit are positive, got `0.0`
after
[policyengine.py#280](https://github.com/PolicyEngine/policyengine.py/pull/280)
moved the UK extra from `policyengine-uk==2.74.0` to `==2.88.0` and
raised the `policyengine_core` floor from 3.23.6 to 3.24.1.

It was not a PolicyEngine UK bug. policyengine-core 3.24.0 to 3.24.3
discarded inputs that a country package set before applying a reform
during simulation construction, the pattern `policyengine_uk.Simulation`
uses.
[policyengine-core#475](https://github.com/PolicyEngine/policyengine-core/pull/475)
fixed this in core 3.24.4, and
[policyengine.py#283](https://github.com/PolicyEngine/policyengine.py/pull/283)
raised policyengine.py's core floor to 3.25.0, both on 18 April 2026.

On 22 October 2026 all eight UK cases in policyengine.py's
`TestUKCalculateHousehold` (`tests/test_household_impact.py`, which
replaced `TestUKHouseholdImpact` in the v4 launch) passed on its main CI
with policyengine-uk 2.132.6, so #1628 can be closed.
```

## What went wrong

policyengine-core's changelog for 3.24.4 describes the bug: its cache
invalidation after `apply_reform` "wiped every variable's
`_memory_storage._arrays`, which also wiped user-provided dataset inputs
loaded via `set_input`. Country-package subclasses calling `set_input`
during construction and then applying a structural reform (the
`policyengine-uk` pattern) silently lost their datasets." In the failing
tests, inputs such as age, `employment_income` and `would_claim_*` were
gone before any calculation ran, so tax and benefits came out as zero.

Two other explanations were considered and do not fit the harness code
at policyengine.py#280's head (`6772ecc`):

- **The dataset-required change** (policyengine-uk 2.76.0, where
  `Simulation()` with no situation, no dataset and no
  `POLICYENGINE_UK_DEFAULT_DATASET` raises a `ValueError`). The harness
  passed an explicit dataset (`Microsimulation(dataset=...)` in
  `src/policyengine/tax_benefit_models/uk/model.py`), so it never reached
  that path.
- **The default period** (`default_input_period` and
  `default_calculation_period`, 2025 in both 2.74.0 and 2.88.0). The
  harness passed `period=` to every calculation, and the failing tests
  built 2026 households.

## Reproduction from the UK side

Two comparable scenarios, run directly against `policyengine-uk` main for
2025 (the failing tests used 2026 and a one-adult, two-child family):

```python
from policyengine_uk import Simulation

YEAR = 2025

# Scenario 1: single adult with employment income.
s1 = {
    "people": {"adult": {"age": {YEAR: 30}, "employment_income": {YEAR: 50_000}}},
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {"household": {"members": ["adult"]}},
}
sim = Simulation(situation=s1)
print("income_tax:", sim.calculate("income_tax", YEAR).sum())
# -> 7486.00

# Scenario 2: couple with one child.
s2 = {
    "people": {
        "a1": {"age": {YEAR: 35}, "employment_income": {YEAR: 30_000}},
        "a2": {"age": {YEAR: 33}},
        "c1": {"age": {YEAR: 5}},
    },
    "benunits": {"benunit": {"members": ["a1", "a2", "c1"]}},
    "households": {"household": {"members": ["a1", "a2", "c1"]}},
}
sim = Simulation(situation=s2)
print("child_benefit:", sim.calculate("child_benefit", YEAR).sum())
# -> 1354.60
```

Re-checked on 23 October 2026 on policyengine-uk 2.148.2 (policyengine-core
3.33.2): both scenarios return £7,486 and £1,354.60. Both also return
non-zero values for every year from 2022 to 2025. The income-tax figure is
the same each year because the personal allowance (£12,570), the basic
rate limit (£37,700) and the 20% basic rate are unchanged from 2021-22;
child benefit follows the eldest-child rate (£1,133.60 in 2022, £1,248.00
in 2023, £1,331.20 in 2024).

## References

- Issue: [#1628](https://github.com/PolicyEngine/policyengine-uk/issues/1628).
- Where the failure showed: [`PolicyEngine/policyengine.py#280`](https://github.com/PolicyEngine/policyengine.py/pull/280) (closed without merging, superseded by #282).
- The fix: [`PolicyEngine/policyengine-core#475`](https://github.com/PolicyEngine/policyengine-core/pull/475) (core 3.24.4) and [`PolicyEngine/policyengine.py#283`](https://github.com/PolicyEngine/policyengine.py/pull/283) (core floor 3.25.0).
- Default-period contract: [`policyengine_uk/simulation.py`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/simulation.py) (`default_input_period`, `default_calculation_period`).
- Default-dataset env var contract: `POLICYENGINE_UK_DEFAULT_DATASET`,
  defined in [`policyengine_uk/tax_benefit_system.py`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/tax_benefit_system.py)
  and read in `policyengine_uk/simulation.py`.
