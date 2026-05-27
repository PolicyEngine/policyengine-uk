# Future-dating policy announcements

PolicyEngine UK supports modelling policy changes that have been
**announced but not yet implemented**, or that take effect at a known
future date. The mechanism is the same one that handles legislated rate
schedules: parameters in `policyengine_uk/parameters/` carry a list of
values keyed by effective date.

This was originally requested in [#636](https://github.com/PolicyEngine/policyengine-uk/issues/636)
in the context of the Truss "growth plan" announcements in autumn 2022.
The feature has been live and well-exercised since the model moved to
date-keyed parameter values; this page documents the current usage
pattern so that future analyses don't need to reinvent it.

## How it works

Every parameter is a `values:` map from effective-date to value. When
the simulation queries a parameter for a given period, the model picks
the value whose date is the **latest one on or before** the queried
date.

Example from
[`gov/hmrc/income_tax/allowances/personal_allowance/amount.yaml`](../../../policyengine_uk/parameters/gov/hmrc/income_tax/allowances/personal_allowance/amount.yaml):

```yaml
values:
  ...
  2027-04-06: 12_570
  2030-04-06:
    value: 12_570
    metadata:
      reference:
        - title: Autumn Budget 2026 — PA freeze extended to 2030-31
          href: https://www.gov.uk/government/publications/autumn-budget-2026
```

The 2030-04-06 entry encodes a **future-dated** policy decision (the
PA freeze extension). Until that date is reached in real time, querying
`personal_allowance.amount(period="2029")` returns £12,570 from the
2027-04-06 row; from `period="2030"` onwards the 2030-04-06 row's value
applies.

## Patterns for common cases

### Announced but reversed before taking effect

Some announcements are walked back before the effective date — the
Truss "growth plan" basic-rate cut to 19% (announced September 2022,
reversed October 2022) is the canonical example. To represent this
honestly:

1. Add the announced value at the announced effective date with a
   reference to the announcement.
2. Add a *second* row at the reversal date with the original value (or
   the actual landing value) and a reference to the reversal
   announcement.

This means a date-stamped baseline (e.g. `policy_date="2022-09-28"`)
will show the reform, and a later date-stamped baseline will show the
reversal. PolicyEngine UK supports this kind of "what did the model
think the world looked like on date X" query.

### Phased-in or staggered changes

Phased rate changes are the most common future-dating pattern. Each
phase is a row at its effective date with a separate `reference`. The
`national_insurance/class_1/thresholds/primary_threshold.yaml`
trajectory through the 2022 Health and Social Care Levy and the
April 2024 cuts is a good worked example.

### Announced abolitions

For an abolition that hasn't yet taken effect (e.g. the [2025 Budget
two-child limit removal](../validation/child-poverty-tcl.md)):

- The relevant parameter (`gov.dwp.universal_credit.elements.child.limit.child_count`)
  has its limiting value (2) up to the announced effective date
  (2026-04-06) and `.inf` from that date onwards.
- Until April 2026, queries return 2 and the model behaves as if the
  limit is in force.
- From April 2026, queries return `.inf` and the limit silently
  vanishes from the UC child element calculation.

The same pattern applies in reverse for sunset clauses (a Cost-of-Living
Payment whose value goes back to zero at a stated date, see
[`changelog/609.md`](https://github.com/PolicyEngine/policyengine-uk/blob/main/changelog.d/609.md)).

## Best practices

1. **Cite the announcement in `metadata.reference`** at every
   future-dated row. The convention through the repo is to include both
   the press-release URL and the formal regulation / statutory
   instrument once it's published — see the multi-row references on
   `national_insurance/class_1/rates/employer.yaml` for an example.
2. **Don't extrapolate**. Each future-dated row should reflect a
   specific announcement. If a parameter would otherwise drift via
   uprating, let `policyengine-core`'s uprating handle that automatically
   — adding a "frozen forever" row is a policy assertion that needs its
   own reference.
3. **Use the `policy_date` query** for back-cast scenarios. If you need
   to recover "what the model thought the world looked like as of
   2022-09-30" (post-mini-budget, pre-reversal), pass that date when
   constructing the simulation.

## What this isn't

This is not the same as **scenario analysis** or **policy reform**
parameters under `gov.contrib.*`. Those are reform-side toggles for
hypothetical changes the user wants to evaluate; future-dated parameter
rows under `gov.hmrc.*`, `gov.dwp.*` etc. are **baseline** policy
representing what is actually announced.

If a future change is uncertain or contested, model it under
`gov.contrib.*` until it's announced; once announced, move it into the
baseline tree with an effective-date row.

## References

- Issue [#636](https://github.com/PolicyEngine/policyengine-uk/issues/636) — original Truss-era future-dating ask.
- PolicyEngine blog post: [Tax cuts in Prime Minister Truss's growth plan 2022](https://blog.policyengine.org/tax-cuts-in-prime-minister-trusss-growth-plan-2022-a4a862892dc1) — worked example of modelling an announcement before reversal.
- [PolicyEngine Core date-keyed parameter API](https://github.com/PolicyEngine/policyengine-core) — underlying mechanism.
- Validation example using a real future-dated change: [child-poverty-tcl.md](../validation/child-poverty-tcl.md) (#1398).
