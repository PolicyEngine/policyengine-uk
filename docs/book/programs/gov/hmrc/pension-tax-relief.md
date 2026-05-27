# Pension tax relief

This page documents how PolicyEngine UK models tax relief on personal
pension contributions and addresses the confusion reported in
[#704](https://github.com/PolicyEngine/policyengine-uk/issues/704)
about whether higher-rate taxpayers receive the right amount of
relief.

## What the model does

`pension_contributions_relief` (defined in
[`variables/gov/hmrc/pensions/pension_contributions_relief.py`](../../../policyengine_uk/variables/gov/hmrc/pensions/pension_contributions_relief.py))
reduces the person's taxable income by the amount of their pension
contribution, capped at:

- the higher of `pension_annual_allowance` (currently £60,000) and the
  `gov.hmrc.income_tax.reliefs.pension_contribution.basic_amount`
  (£3,600 — the unearned-income contribution ceiling),
- the person's total earned income (employment + self-employment),
- subject to the `pension_contributions_relief_age_limit` (75).

Contributions **above** the annual allowance trigger a separate
charge — `personal_pension_contributions_tax` — which taxes the
excess at the person's marginal rate.

So the headline behaviour is: **within the annual allowance, pension
contributions reduce taxable income £1-for-£1**. The income-tax saving
that the model reports is the contribution × the person's marginal
rate.

## Worked examples

The four scenarios reported in #704 (all 2025-26, all self-employed,
single person, no other income):

| ID    | Self-employed income | Pension contribution | Expected income-tax change | What the model returns | Why |
|-------|---------------------|----------------------|-----------------------------|------------------------|-----|
| 11800 | £30,000             | £0                   | baseline                    | baseline               | – |
| 11799 | £30,000             | £3,000               | -£600                       | -£600                  | £3k contribution × 20% basic rate |
| 11817 | £60,000             | £0                   | baseline                    | baseline               | – |
| 11816 | £60,000             | £6,000               | -£2,400                     | -£2,400                | £6k contribution × 40% higher rate |

This is exactly the behaviour reported. The user's expectation that
higher-rate cases should only see -£1,200 (£6k × 20%) corresponds to a
misunderstanding of how UK pension tax relief works in aggregate: the
total tax relief is full marginal rate, even though it is paid in two
parts in the real world (relief at source plus higher-rate top-up via
Self Assessment).

## Relief at source vs marginal-rate relief

The user-facing UK pension framework has two parallel mechanisms that
add up to the same total relief:

1. **Relief at source (RAS)** — the pension provider claims the
   basic-rate portion (20%) directly from HMRC. The contributor pays
   from net income and the pension grows by the gross amount. For a
   basic-rate taxpayer, this is the *entire* relief.
2. **Higher-rate top-up** — for taxpayers at higher or additional
   rates, the extra band difference (20% for higher rate, 25% for
   additional) is reclaimed via Self Assessment. The mechanism is
   technically a **basic-rate-band extension**: HMRC widens the basic
   rate band by the gross contribution, pushing income that would
   otherwise be taxed at the higher rate down into the basic band.

PolicyEngine computes the **total** relief — both mechanisms together —
because it operates on annual aggregates rather than walking the
cash-flow steps. That matches HMRC's published statistics on the
*fiscal cost of pension tax relief*, which also report the total
across both mechanisms.

If you want to see the user-visible tax bill reduction separately from
the pension-provider's RAS claim, you'd need to split the existing
relief into two output variables (a basic-rate-portion and a
higher-rate-top-up portion). This is a presentation question rather
than a calculation question — the totals are unchanged.

## Marginal tax rate display

#704 also reported a 0% marginal tax rate where 20% / 40% was
expected. The marginal-tax-rate calculation is a frontend concern
(the policyengine.org app derives it numerically by perturbing income),
so it depends on which variable is being differentiated. PolicyEngine
UK exposes a clean `income_tax` that, when differentiated against
`employment_income` or `self_employment_income`, returns the
person's marginal rate; if the frontend is differentiating against a
different variable (e.g. `household_net_income` net of taper effects)
it can return values that look surprising. This is out of scope for
the model repo.

## References

- HMRC, [Tax on your private pension contributions: Tax relief](https://www.gov.uk/tax-on-your-private-pension/pension-tax-relief) — user-facing guide to RAS + higher-rate relief.
- [Finance Act 2004 s. 188-194](https://www.legislation.gov.uk/ukpga/2004/12/section/188) — primary statute for relief-at-source.
- [Finance Act 2004 s. 227](https://www.legislation.gov.uk/ukpga/2004/12/section/227) — annual allowance excess charge.
- HMRC, [Pension tax relief statistics](https://www.gov.uk/government/collections/personal-pensions-statistics) — published costing methodology used for the calibration target.
- Model variables: [`pension_contributions_relief`](../../../policyengine_uk/variables/gov/hmrc/pensions/pension_contributions_relief.py) and [`personal_pension_contributions_tax`](../../../policyengine_uk/variables/gov/hmrc/pensions/private_pension_contributions_tax.py).
