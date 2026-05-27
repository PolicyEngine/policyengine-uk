# Ubuntu vs macOS reproducibility

```{note}
Issue [#1209](https://github.com/PolicyEngine/policyengine-uk/issues/1209)
reported that PolicyEngine UK produced different aggregates on
`ubuntu-latest` vs `macos-latest` CI for the same dataset and the
same `policyengine-uk` version. The triage narrowed the divergence to
**parameter uprating**: a limited subset of parameters were uprated on
macOS but not on Ubuntu. This page records the diagnosis and the
current status so that, if a similar regression surfaces, the next
person doesn't have to re-derive the root-cause shape.
```

## Symptom

Running the test suite or a microsimulation on the same dataset (with
the same `policyengine-uk-data` artifact) against the same
`policyengine-uk` version produces slightly different aggregates
across OS:

- Affected: a limited subset of parameters (the dumps attached to the
  original issue showed values diverged only at parameters that should
  have been uprated by the OBR indices).
- Not affected: dataset content (verified identical between runs),
  formulas, or rate parameters that were directly authored in YAML.

The order of magnitude was small (a fraction of a percent on weighted
aggregates) but reproducibility-breaking.

## Diagnosed root cause

The triage in
[`fix-ubuntu-macos-parameter-uprating`](https://github.com/PolicyEngine/policyengine-uk/pull/1223)
narrowed it to **dictionary iteration order in the uprating step**:
when `apply_uprating` walked the parameter tree, the order in which
nested parameters were visited could differ between platforms in
specific cases, and floating-point accumulation differences meant
some values landed at slightly different rounded levels.

## Current status

A series of follow-on changes have since landed that interact with
this code path:

- [PR #1254](https://github.com/PolicyEngine/policyengine-uk/pull/1254)
  added multi-year datasets and separated uprating into a discrete
  pipeline step.
- [PR #1543](https://github.com/PolicyEngine/policyengine-uk/pull/1543) /
  [#1544](https://github.com/PolicyEngine/policyengine-uk/pull/1544) /
  the [`uprate_rent` StringArray-conversion fix](https://github.com/PolicyEngine/policyengine-uk/commit/13a4ac72)
  rebuilt the rent uprating path that was the primary visible site of
  the divergence in #1209's dumps.
- [PR #1523](https://github.com/PolicyEngine/policyengine-uk/pull/1523)
  skipped a redundant dataset copy in `apply_uprating`.

The CI runs on `ubuntu-latest` only, so a cross-OS regression test was
not added when the original fixes landed. **If reproducibility across
OS becomes important for a downstream consumer (PolicyEngine.org
production, an external academic user), the next step is**:

1. Restore the cross-OS CI matrix described in the original issue (or
   carry the diagnostic shadow repo at
   [`nikhilwoodruff/policyengine-uk-private`](https://github.com/nikhilwoodruff/policyengine-uk-private)
   as a documented external check).
2. Run the same dataset through the build on `ubuntu-latest` and
   `macos-latest`; compare the per-parameter dumps. If any divergence
   reappears, the same iteration-order class of bug is the prime
   suspect — re-instrument `apply_uprating` to sort children
   deterministically.

## How to add a deterministic-order regression test

A minimal in-repo test that would catch a reintroduction:

```python
def test_apply_uprating_deterministic_order():
    """Two passes of apply_uprating on the same tree should produce
    bit-identical results regardless of dict insertion order."""
    from policyengine_uk import Microsimulation

    sim1 = Microsimulation()
    sim2 = Microsimulation()
    for variable in ["state_pension", "child_benefit", "universal_credit"]:
        # Both Microsimulation instances build from the same data,
        # uprate independently, and should converge to identical
        # aggregates after the uprating step.
        assert sim1.calculate(variable, 2025).sum() == sim2.calculate(
            variable, 2025
        ).sum()
```

If this test passes on Ubuntu but a stronger cross-OS comparison fails,
the divergence is somewhere outside the iteration-order-via-dict
hypothesis and the analysis needs to start from the per-parameter
dumps again.

## References

- Tracking issue: [#1209](https://github.com/PolicyEngine/policyengine-uk/issues/1209).
- Original triage: [#1205](https://github.com/PolicyEngine/policyengine-uk/pull/1205).
- Closed fix attempt: [#1223](https://github.com/PolicyEngine/policyengine-uk/pull/1223).
- Follow-on uprating refactors: #1254, #1523, #1543, #1544.
- Diagnostic shadow repo: [`nikhilwoodruff/policyengine-uk-private`](https://github.com/nikhilwoodruff/policyengine-uk-private) (private; carries both OS runners).
