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

Every parameter is a `values:` map from effective date to value. When
the tax-benefit system is built, `convert_to_fiscal_year_parameters`
(`policyengine_uk/utils/parameters.py`) turns each parameter into one
value per model year, where model year 2026 is the fiscal year 6 April
2026 to 5 April 2027:

- by default, the value in force on 30 April of that year;
- for parameters with `fiscal_year_blend: true` in their metadata (fuel
  duty, for example), the day-weighted average over the fiscal year, so a
  change part-way through the year counts for the share of the year it
  applies;
- parameters with `preserve_calendar_dates: true` keep their statutory
  dates, and their formulas annualise explicitly.

Example from
[`gov/hmrc/income_tax/allowances/personal_allowance/amount.yaml`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/parameters/gov/hmrc/income_tax/allowances/personal_allowance/amount.yaml):

```yaml
values:
  ...
  2021-04-06: 12_570
  2027-04-06: 12_570
  2030-04-06:
    value: 12_570
    metadata:
      reference:
        - title: OBR Economic and Fiscal Outlook November 2025
          href: https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/
```

The 2030-04-06 row records a future-dated decision: the freeze extended
to 2030-31 at the 2025 Budget. Without it, uprating would move the
allowance from 2028 onwards; with it, model years up to 2030 return
£12,570.

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

The baseline then follows what was finally enacted. PolicyEngine UK has
no "policy as announced on date X" switch, so to score an announcement as
it stood before a reversal, apply it as a reform (see
the [excise duties page](../../engineering/excise-duties.md) for how
dated reforms are annualised).

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
- Model year 2025 (fiscal year 2025-26) returns 2, so the limit applies.
- From model year 2026 the value is `.inf`, so the limit no longer
  restricts the UC child element.

The same pattern applies in reverse for sunset clauses (a Cost-of-Living
Payment whose value goes back to zero at a stated date, see
[`changelog.d/609.md`](https://github.com/PolicyEngine/policyengine-uk/blob/main/changelog.d/609.md)).

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
3. **Check how the parameter is annualised.** A change dated part-way
   through a fiscal year only counts for part of the year if the
   parameter has `fiscal_year_blend: true`; otherwise the model year takes
   the value in force on 30 April.

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
- PolicyEngine research: [Tax cuts in Prime Minister Truss's growth plan](https://www.policyengine.org/uk/research/tax-cuts-in-prime-minister-trusss-growth-plan) — worked example of modelling an announcement before reversal.
- [PolicyEngine Core date-keyed parameter API](https://github.com/PolicyEngine/policyengine-core) — underlying mechanism.
- Validation example using a real future-dated change: [child-poverty-tcl.md](../validation/child-poverty-tcl.md) (#1398).
