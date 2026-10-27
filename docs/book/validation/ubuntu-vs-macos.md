# Ubuntu vs macOS reproducibility

```{note}
Issue [#1209](https://github.com/PolicyEngine/policyengine-uk/issues/1209)
reported that PolicyEngine UK gave different results on `ubuntu-latest`
and `macos-latest` for the same dataset and the same `policyengine-uk`
version. The cause was in parameter uprating. As of October 2026 the
parameter tree is byte-identical across macOS and Linux, and CI has moved
back to Linux. This page records the diagnosis, the fix and how to check
for a regression.
```

## Symptom

This divergence was spotted in
[#1205](https://github.com/PolicyEngine/policyengine-uk/pull/1205),
whose results differed between the two runners. It was the second such
case: [#1091](https://github.com/PolicyEngine/policyengine-uk/issues/1091)
(April 2025) had found benefit parameters that uprated on macOS but not
on Ubuntu, and [#1092](https://github.com/PolicyEngine/policyengine-uk/pull/1092)
fixed that one. A diagnostic repository that ran the same code on both
runners and stored the full entity dataset as artifacts showed that:

- the input data were identical on both operating systems;
- a limited subset of parameters was uprated on macOS but not on
  Ubuntu. Parameter-tree dumps attached to a
  [later comment on #1209](https://github.com/PolicyEngine/policyengine-uk/issues/1209#issuecomment-3062418736)
  show 82 Department for Work and Pensions parameters, all uprated
  through `gov.benefit_uprating_cpi`, that were uprated on macOS but
  kept their set values on Ubuntu.

No record gives the size of the effect on aggregates, but it broke
reproducibility.

## Cause

The dumps show where the trees differed: the 82 parameters differ only
in the main tree, while their `parameters.baseline` copies match. At the
time `gov.benefit_uprating_cpi` held only a 2005 value and was itself
uprated from `gov.obr.consumer_price_index`, so these were chained
upratings (a parameter uprated from an index that is itself uprated), the
case #1092 had found in April 2025. policyengine-core then loaded each
parameter directory in unsorted `os.listdir` order, which can differ
between file systems, and uprating depended on the order in which it
reached the parameters, so a parameter reached before its uprating index
had been extended got no new values.
[policyengine-core#490](https://github.com/PolicyEngine/policyengine-core/issues/490)
later described the same failure in policyengine-us. The order the 2025
runners actually listed the files in was never recorded, so this is
inferred from the code and the dumps rather than traced.

[#1223](https://github.com/PolicyEngine/policyengine-uk/pull/1223)
(closed without merging) proposed a different cause: that the uprating
growth-factor table (`BASELINE_GROWFACTORS`) was computed at import time,
before the system was initialised. That table only read parameter values
and, as called (`print_diff=False`), returned the stored
`uprating_growth_factors.csv`, so it could not change the parameter tree.

## How it was resolved

- [#1092](https://github.com/PolicyEngine/policyengine-uk/pull/1092)
  (April 2025) added `macos-latest` alongside `ubuntu-latest` to the
  pull-request Test job and fixed the first case, #1091. When #1209
  appeared, [#1205](https://github.com/PolicyEngine/policyengine-uk/pull/1205)
  dropped `ubuntu-latest` from that job to unblock itself, and
  [#1207](https://github.com/PolicyEngine/policyengine-uk/pull/1207)
  moved the main-branch Test job to `macos-latest` (both July 2025).
- [#1254](https://github.com/PolicyEngine/policyengine-uk/pull/1254)
  (multi-year datasets, with uprating as a separate step) removed the
  import-time `BASELINE_GROWFACTORS` table that #1223 had suspected.
  Dataset uprating is now applied by `apply_uprating` in
  [`policyengine_uk/data/economic_assumptions.py`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/data/economic_assumptions.py).
  Parameter uprating is policyengine-core's `uprate_parameters`, called
  from `policyengine_uk/tax_benefit_system.py`.
- Later fixes to the dataset uprating path:
  [#1523](https://github.com/PolicyEngine/policyengine-uk/pull/1523)
  (no redundant dataset copy in `apply_uprating`),
  [#1543](https://github.com/PolicyEngine/policyengine-uk/pull/1543) and
  [#1544](https://github.com/PolicyEngine/policyengine-uk/pull/1544)
  (`uprate_rent` lookups).
- policyengine-core now sorts each directory listing when it loads the
  parameter tree, and uprates each parameter after the index it is
  uprated from
  ([policyengine-core#491](https://github.com/PolicyEngine/policyengine-core/pull/491),
  May 2026), so neither load order nor the file system can change
  uprated values.

On 3 October 2026 the Test job moved from macOS to `ubuntu-24.04-arm`
(commit
[`67c63861`](https://github.com/PolicyEngine/policyengine-uk/commit/67c638613),
in [#2115](https://github.com/PolicyEngine/policyengine-uk/pull/2115)).
That change verified, on main at `3c48247e`, that:

- the full parameter tree (2,706 parameter objects and 43,666 dated
  values, including the baseline copies) is byte-identical on macOS
  arm64, `ubuntu-latest` and `ubuntu-24.04-arm`;
- the YAML tests pass on both Linux runners;
- every pytest outcome matches the macOS run of the same code, test by
  test.

#1209 can be closed on that evidence.

## Checking for a regression

CI now runs the test suite (`.github/workflows/test-suite.yaml`: the
YAML tests in one job and the Python tests split over six shards) on
Linux arm64 (`ubuntu-24.04-arm`), and the install and smoke-import checks
on x86 `ubuntu-latest`. There is no macOS job. If an OS difference is
suspected again:

1. Dump the processed parameter tree on each platform (every parameter
   and every dated value, including `parameters.baseline`) and compare
   checksums. This is the check the October 2026 move relied on.
2. If the trees differ, look first at chained uprating (a parameter
   uprated from an index that is itself uprated) and at anything else
   that depends on file or dictionary order.
3. If the trees match but results differ, compare the uprated dataset
   variables next. #1209 showed the input data themselves were the same
   on both systems.

## References

- Tracking issue: [#1209](https://github.com/PolicyEngine/policyengine-uk/issues/1209).
- Where this difference was seen: [#1205](https://github.com/PolicyEngine/policyengine-uk/pull/1205); the earlier case: [#1091](https://github.com/PolicyEngine/policyengine-uk/issues/1091), fixed by #1092.
- A proposed cause that did not hold: [#1223](https://github.com/PolicyEngine/policyengine-uk/pull/1223) (closed without merging).
- Order-independent uprating: [policyengine-core#490](https://github.com/PolicyEngine/policyengine-core/issues/490), [#491](https://github.com/PolicyEngine/policyengine-core/pull/491).
- CI moved to macOS: #1092 (macOS alongside Ubuntu), #1205 and #1207 (macOS only); moved back to Linux: [`67c63861`](https://github.com/PolicyEngine/policyengine-uk/commit/67c638613) (#2115).
- Uprating rebuild and follow-ups: #1254, #1523, #1543, #1544.
