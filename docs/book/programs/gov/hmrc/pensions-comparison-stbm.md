# Pension treatment compared with the Scottish Tax-Benefit Model

This page documents how PolicyEngine UK's handling of personal pension
contributions compares with the [Scottish Tax-Benefit Model (STBM)
methodology][stbm-blog] described in the Virtual Worlds blog. It
addresses [#672](https://github.com/PolicyEngine/policyengine-uk/issues/672).

Read alongside [pension-tax-relief.md](./pension-tax-relief.md), which
explains the PolicyEngine pension-relief mechanics in detail.

## Summary

Both models compute the **same total tax cost** of pension tax relief
at the aggregate level for a given household, but they differ in how
the relief is presented:

|                                       | PolicyEngine UK                                | Scottish Tax-Benefit Model                             |
|---------------------------------------|------------------------------------------------|--------------------------------------------------------|
| Treatment of within-allowance contribution | Reduce taxable income by gross contribution    | Same                                                   |
| Relief mechanism in code              | Single `pension_contributions_relief` variable | Split between relief-at-source and basic-rate-band extension |
| Excess-over-allowance treatment       | Separate `personal_pension_contributions_tax` charge at marginal rate | Same |
| Salary sacrifice                      | `pension_contributions_via_salary_sacrifice` input; deducted from earnings before NI; affects employer NI cost | Same in principle |
| Employer contributions                | `employer_pension_contributions` input; excluded from earnings for income tax and NI | Same |
| State Pension                         | Three composable variables (`basic_state_pension`, `new_state_pension`, `additional_state_pension`) with triple-lock uprating | Modelled as a single uprated transfer |

## Where the two models could diverge

### 1. Presentation of relief at source vs the higher-rate top-up

STBM (as described in the Virtual Worlds blog) tends to keep the
**relief-at-source** portion (basic-rate, paid into the pension pot)
separate from the **higher-rate top-up** (paid back to the taxpayer via
Self Assessment). PolicyEngine UK combines both into a single
`pension_contributions_relief` reduction in taxable income.

Why it doesn't change the answer: at the *household-level fiscal cost*,
both methods produce identical totals. HMRC's *pension tax relief
statistics* — which both models target for calibration — report the
combined relief.

Where it would change the answer: a user who wants to break out the
"cash visible to the taxpayer" portion of their tax bill needs the
split version (because their own SA refund is only the higher-rate
top-up). PolicyEngine UK would need an output split into two new
variables (`pension_relief_at_source` and `pension_higher_rate_top_up`)
to surface this distinction — discussed in
[pension-tax-relief.md](./pension-tax-relief.md).

### 2. Annual allowance taper

For high earners (adjusted income > £260,000 since 2023-24), the
annual allowance is tapered. PolicyEngine UK encodes this through:

- `gov/hmrc/income_tax/allowances/annual_allowance/taper.yaml`
- `gov/hmrc/income_tax/allowances/annual_allowance/reduction_rate.yaml`
- `gov/hmrc/income_tax/allowances/annual_allowance/minimum.yaml`

STBM applies the same taper mechanically. The two diverge only if
STBM's modelling of the *adjusted-income* trigger differs from
PolicyEngine UK's `meets_marriage_allowance_income_conditions`-style
piecewise calculations.

### 3. Carry-forward of unused allowance

UK rules allow carrying forward unused annual allowance from the
previous three tax years. **Neither** PolicyEngine UK nor (as of the
linked blog) STBM models this — both treat the annual allowance as
strictly per-year.

For most households this doesn't matter; the carry-forward is mainly
used by people with lumpy contributions (one-off bonus / sale events).
Either model would need an explicit `unused_annual_allowance_carryforward`
input to handle this correctly.

### 4. Lifetime allowance (abolished from 6 April 2024)

PolicyEngine UK historically tracked the lifetime allowance under
`gov/hmrc/pensions/`. From 6 April 2024 the lifetime allowance was
abolished and replaced by the **lump sum allowance** and **lump sum
and death benefit allowance**. PolicyEngine UK and STBM both need
parameters here; current PolicyEngine UK status:

- the historical lifetime-allowance values remain in the parameter tree
  for back-cast simulations,
- the post-2024 lump sum allowances are not yet modelled, as they
  rarely affect ordinary income-tax-cost analysis (they only bite at
  withdrawal).

### 5. State Pension structure

PolicyEngine UK uses the three-variable split documented in
[state-pension.md](../dwp/state-pension.md):
`basic_state_pension`, `new_state_pension`, `additional_state_pension`
(SERPS / S2P for BASIC; Protected Payment for NEW). STBM appears to
treat State Pension as a single transfer per the blog — which is
appropriate for headline distributional analysis but obscures the
Protected Payment structure that matters for reform analysis (e.g.
abolishing the triple lock on the new flat rate only).

## Calibration

Both models target HMRC pension tax relief statistics and DWP State
Pension outturn. PolicyEngine UK's residual State Pension undershoot is
documented under [state-pension.md](../dwp/state-pension.md) and
[#1632](https://github.com/PolicyEngine/policyengine-uk/issues/1632);
STBM's calibration variance is not publicly documented in detail.

## What's not modelled in either

- **Pension contribution behavioural response** to tax-rate changes
  (people changing their contribution rate when the higher-rate band
  changes). Both models hold contributions fixed.
- **Decumulation taxation** (income drawn from pensions in retirement)
  beyond the basic `private_pension_income` input — neither model
  walks through crystallisation, the 25% tax-free lump sum, or annuity
  vs. drawdown decisions.

## References

- Virtual Worlds, [STBM blog: Pension contributions][stbm-blog] — the
  reference methodology this page compares against.
- PolicyEngine UK: [pension-tax-relief.md](./pension-tax-relief.md),
  [state-pension.md](../dwp/state-pension.md).
- Variables: [`pension_contributions_relief`](../../../policyengine_uk/variables/gov/hmrc/pensions/pension_contributions_relief.py), [`personal_pension_contributions_tax`](../../../policyengine_uk/variables/gov/hmrc/pensions/private_pension_contributions_tax.py).
- HMRC, [Pension tax relief statistics](https://www.gov.uk/government/collections/personal-pensions-statistics).
- Issue: [#672](https://github.com/PolicyEngine/policyengine-uk/issues/672).

[stbm-blog]: https://stb-blog.virtual-worlds.scot/articles/2022/01/01/pension-contributions.html
