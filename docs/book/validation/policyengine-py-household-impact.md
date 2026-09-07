# Household-impact tests returning 0 (resolved)

```{note}
**Resolved.** [#1628](https://github.com/PolicyEngine/policyengine-uk/issues/1628)
reported that two `policyengine.py` household-impact integration tests
started asserting `0.0` for expected-positive tax and child-benefit
values after bumping the UK extra to `policyengine-uk==2.88.0`. This
page documents the diagnosis from the PolicyEngine UK side and the
guidance for the upstream `policyengine.py` repo. It is not a model
bug — the UK model produces the expected non-zero values when called
correctly.
```

## Reproduction from the UK side

Running the two scenarios directly against `policyengine-uk` main:

```python
from policyengine_uk import Microsimulation
YEAR = 2025

# Scenario 1 — single adult with employment income.
s1 = {
    "people": {"adult": {"age": {YEAR: 30},
                         "employment_income": {YEAR: 50_000}}},
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {"household": {"members": ["adult"]}},
}
sim = Microsimulation(situation=s1)
print("income_tax:", sim.calculate("income_tax", YEAR).sum())
# -> 7486.00

# Scenario 2 — couple with one child.
s2 = {
    "people": {
        "a1": {"age": {YEAR: 35}, "employment_income": {YEAR: 30_000}},
        "a2": {"age": {YEAR: 33}},
        "c1": {"age": {YEAR: 5}},
    },
    "benunits": {"benunit": {"members": ["a1", "a2", "c1"]}},
    "households": {"household": {"members": ["a1", "a2", "c1"]}},
}
sim = Microsimulation(situation=s2)
print("child_benefit:", sim.calculate("child_benefit", YEAR).sum())
# -> 1354.60
```

Both return the expected non-zero values across the range 2022-2025
(the income-tax figure is invariant because the personal allowance is
£12,570 throughout this window). So **the underlying model is healthy**.

## What changed between 2.74 and 2.88

The most likely cause of the upstream test failure is the
**default-period** contract:

```python
# policyengine_uk/simulation.py
class Simulation(CoreSimulation):
    default_input_period: int = 2025
    default_calculation_period: int = 2025
```

If `policyengine.py`'s household-impact harness was building a 2024
situation but the UK model now defaults to 2025 for calculation, any
benefit / tax variable that hadn't been populated for 2025 in the
situation would compute against missing inputs and could return 0.

The other plausible cause is the **dataset-required** invariant in
the `Simulation()` constructor: from
`policyengine_uk==2.79`-ish onwards, `Simulation()` without an
explicit `dataset=` argument and without the
`POLICYENGINE_UK_DEFAULT_DATASET` env var raises a `ValueError`. If
the `policyengine.py` harness was catching that error and falling
through to a degenerate code path (zero-filled `Microsimulation`),
the tests would see zeros.

## Guidance for the upstream fix

The `policyengine.py` household-impact harness should:

1. Pass an **explicit `period`** to every `calculate(...)` call
   matching the year encoded in the situation YAML, rather than relying
   on the model default.
2. Build the situation using the **`Microsimulation(situation=...)`**
   form rather than the dataset-backed `Simulation()` — single-household
   queries don't need a dataset and shouldn't bring in the default-
   dataset env-var dependency.
3. **Assert against the year encoded in the test fixture**, not the
   model's `default_input_period`. The fixture-encoded year is what the
   test author intended.

The two failing tests should produce ~£7,486 income tax for a
£50k-earning single adult and ~£1,354.60 of child benefit for a
couple-with-one-child benefit unit at 2025 rates.

## Why this is documented in `policyengine-uk` rather than fixed there

The actual fix lives in `policyengine.py`'s test harness and is
explicitly out of scope for this repo (sister-repo edits aren't
made from `policyengine-uk`). This page exists so the next reviewer
who sees `#1628` and is unfamiliar with the policyengine.py setup has
a one-stop diagnosis instead of having to re-derive it.

## References

- Issue: [#1628](https://github.com/PolicyEngine/policyengine-uk/issues/1628).
- Reproducer: [`PolicyEngine/policyengine.py#280`](https://github.com/PolicyEngine/policyengine.py/pull/280).
- Default-period contract: [`policyengine_uk/simulation.py`](../../../policyengine_uk/simulation.py) (`default_input_period`, `default_calculation_period`).
- Default-dataset env var contract: documented in
  [mp30k-uk-switch-plan.md](../assumptions/mp30k-uk-switch-plan.md#current-state).
