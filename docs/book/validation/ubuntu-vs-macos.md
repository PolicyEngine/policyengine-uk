# Ubuntu vs macOS reproducibility

```{note}
Issue [#1209](https://github.com/PolicyEngine/policyengine-uk/issues/1209)
reported that PolicyEngine UK produced different aggregates on
`ubuntu-latest` and `macos-latest` for the same dataset and the same
`policyengine-uk` version. The cause was in parameter uprating. As of
October 2026 the parameter tree is byte-identical across macOS and
Linux, and CI has moved back to Linux. This page records the diagnosis,
the fix and how to check for a regression.
```

## Symptom

The divergence was first spotted in
[#1205](https://github.com/PolicyEngine/policyengine-uk/pull/1205),
whose results differed between the two runners. A diagnostic
repository that ran the same code on both runners and stored the full
entity dataset as artifacts showed that:

- the input data were identical on both operating systems;
- a limited subset of parameters was uprated on macOS but not on
  Ubuntu (the parameter-tree dumps are attached to
  [#1209](https://github.com/PolicyEngine/policyengine-uk/issues/1209#issuecomment-3062418736)).

The effect on weighted aggregates was small, but it broke
reproducibility.

## Cause

[#1223](https://github.com/PolicyEngine/policyengine-uk/pull/1223)
(closed without merging) traced it to an **import-time ordering
problem**: the uprating growth-factor table
(`BASELINE_GROWFACTORS = create_policyengine_uprating_factors_table()`)
was computed when its module was imported, before the parameter tree
had been fully processed. Whether the tree was ready by then depended
on the order in which modules and parameter files were loaded, and that
order differed between the two operating systems.

## How it was resolved

- [#1092](https://github.com/PolicyEngine/policyengine-uk/pull/1092)
  and [#1207](https://github.com/PolicyEngine/policyengine-uk/pull/1207)
  ran the Test job on `macos-latest` in 2025, so that CI matched the
  platform that gave the expected results.
- [#1254](https://github.com/PolicyEngine/policyengine-uk/pull/1254)
  (multi-year datasets, with uprating as a separate step) removed the
  import-time `BASELINE_GROWFACTORS` table. Uprating is now applied by
  `apply_uprating` in
  [`policyengine_uk/data/economic_assumptions.py`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/data/economic_assumptions.py).
- Later fixes to the same path:
  [#1523](https://github.com/PolicyEngine/policyengine-uk/pull/1523)
  (no redundant dataset copy in `apply_uprating`),
  [#1543](https://github.com/PolicyEngine/policyengine-uk/pull/1543) and
  [#1544](https://github.com/PolicyEngine/policyengine-uk/pull/1544)
  (`uprate_rent` lookups).
- policyengine-core now sorts each directory listing when it loads the
  parameter tree, so the load order no longer depends on the file
  system.

On 3 October 2026 the Test job moved from macOS to `ubuntu-24.04-arm`
(commit
[`67c63861`](https://github.com/PolicyEngine/policyengine-uk/commit/67c638613)).
That change verified, on main at `3c48247e`, that:

- the full parameter tree (2,706 parameter objects and 43,666 dated
  values, including the baseline copies) is byte-identical on macOS
  arm64, `ubuntu-latest` and `ubuntu-24.04-arm`;
- the YAML tests pass on both Linux runners;
- every pytest outcome matches the macOS run of the same code, test by
  test.

#1209 can be closed on that evidence.

## Checking for a regression

CI now runs the Test job on Linux arm64 and the smoke imports on x86
`ubuntu-latest`. There is no macOS job. If an OS difference is
suspected again:

1. Dump the processed parameter tree on each platform (every parameter
   and every dated value, including `parameters.baseline`) and compare
   checksums. This is the check the October 2026 move relied on.
2. If the trees differ, look first at anything that runs at import time
   or depends on file or dictionary order.
3. If the trees match but results differ, compare the uprated dataset
   variables next. #1209 showed the input data themselves were the same
   on both systems.

## References

- Tracking issue: [#1209](https://github.com/PolicyEngine/policyengine-uk/issues/1209).
- Where the difference was first seen: [#1205](https://github.com/PolicyEngine/policyengine-uk/pull/1205).
- Diagnosis: [#1223](https://github.com/PolicyEngine/policyengine-uk/pull/1223) (closed).
- CI moved to macOS: #1092, #1207; moved back to Linux: [`67c63861`](https://github.com/PolicyEngine/policyengine-uk/commit/67c638613).
- Uprating rebuild and follow-ups: #1254, #1523, #1543, #1544.
