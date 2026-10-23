# Pension tax relief

This page documents how PolicyEngine UK models tax relief on personal
pension contributions and addresses the confusion reported in
[#704](https://github.com/PolicyEngine/policyengine-uk/issues/704)
about whether higher-rate taxpayers receive the right amount of
relief. #704 is still open (October 2026); the figures below were re-run
on policyengine-uk 2.148.2.

## What the model does

`pension_contributions_relief` (defined in
[`variables/gov/hmrc/pensions/pension_contributions_relief.py`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/hmrc/pensions/pension_contributions_relief.py),
with the limit in `utils/pensions.py`) reduces the person's taxable income
by their pension contributions, up to the annual limit for relief in
[Finance Act 2004 s. 190](https://www.legislation.gov.uk/ukpga/2004/12/section/190):

- the person's relevant UK earnings
  ([s. 189(2)](https://www.legislation.gov.uk/ukpga/2004/12/section/189)),
  which the model takes as taxable employment income: employment income
  plus employer-paid Statutory Sick Pay and Statutory Maternity Pay
  (`employment_benefits`, listed as relevant UK earnings in HMRC's
  [PTM044100](https://www.gov.uk/hmrc-internal-manuals/pensions-tax-manual/ptm044100)),
  less allowable employment expenses; plus trading profit after capital
  allowances and the trading allowance but before losses (a trading loss
  counts as zero, and does not reduce employment earnings). Statutory Paternity Pay is not yet counted;
  open pull request
  [#2368](https://github.com/PolicyEngine/policyengine-uk/pull/2368) would
  add it to taxable employment pay;
- raised towards `gov.hmrc.income_tax.reliefs.pension_contribution.basic_amount`
  (£3,600) where earnings are lower, but only by relief-at-source
  contributions ([s. 191(7)](https://www.legislation.gov.uk/ukpga/2004/12/section/191)).
  The model treats `personal_pension_contributions` as relief at source and
  employee contributions as a net pay arrangement, which cannot use the
  basic amount;
- and only for people under `gov.hmrc.pensions.pension_contributions_relief_age_limit`
  (75).

So someone with no earnings who makes a £3,600 gross contribution to a
personal pension gets a £3,600 `pension_contributions_relief`, while the same
payment as an employee contribution gets none. That £3,600 is the deduction
from taxable income, not a cash top-up. Under relief at source the £3,600
gross contribution is £2,880 paid by the contributor plus £720 (20%) that the
pension provider claims from HMRC and adds to the pension
([Finance Act 2004 s. 192](https://www.legislation.gov.uk/ukpga/2004/12/section/192)).
PolicyEngine does not represent the £720 claim as a payment, and with no
taxable income the deduction saves no income tax. Statutory Sick Pay and
Statutory Maternity Pay were added to relevant earnings by
[#2464](https://github.com/PolicyEngine/policyengine-uk/pull/2464), merged on
19 October 2026.
[#2488](https://github.com/PolicyEngine/policyengine-uk/pull/2488), merged on
20 October 2026, applied the same relief-at-source-only rule to the pension
uplift in adjusted total income.

The annual allowance does not limit the relief. `pension_annual_allowance`
is the standard annual allowance (£60,000 from 6 April 2023). From 2016-17 it
is tapered only when both the statutory adjusted income
(`pension_annual_allowance_adjusted_income`, above £260,000 from 2023-24) and
threshold income (`pension_annual_allowance_threshold_income`, above the
taper level less the standard allowance, £200,000 from 2023-24) are over
their limits, by £1 for every £2 of adjusted income above the taper level,
rounded down to whole pounds, to a minimum of £10,000 (£4,000 from 2020-21
to 2022-23)
([Finance Act 2004 s. 228ZA](https://www.legislation.gov.uk/ukpga/2004/12/section/228ZA);
parameters under `gov.hmrc.income_tax.allowances.annual_allowance`). See
`docs/engineering/pension-annual-allowance.md` for the income conventions.
Unused allowance carried forward from the previous three tax years
([s. 228A](https://www.legislation.gov.uk/ukpga/2004/12/section/228A)) is
`unused_pension_annual_allowance`, which is added to the allowance when the
charge is worked out. It can be supplied for a year. Otherwise, because
survey data does not record past pension input amounts, from 2020-21 the
model estimates it: it assumes that in each of the five previous years the
pension input and the incomes tested for the taper were this year's (times
`gov.simulation.pensions.prior_year_input_ratio`, 1, for the input), deflated
by average earnings growth, and carries forward what the last three years'
allowances leave unused, after each year's excess has used the unused
allowance of the three years before it, earliest first (s. 228A(7)). The estimate is nil for someone with
no pension input this year, and nil before 2020-21. The money purchase
annual allowance, the £10,000 limit on money purchase savings after pensions
are first flexibly accessed
([s. 227ZA](https://www.legislation.gov.uk/ukpga/2004/12/section/227ZA)),
is not modelled.

Contributions **above** the annual allowance can still be relieved and
separately attract the annual allowance charge,
`personal_pension_contributions_tax`, which is added to income tax. It charges
the excess at the basic, higher and additional rates on the slices that fall
in each band when it is added on top of the person's income after allowances
([Finance Act 2004 s. 227](https://www.legislation.gov.uk/ukpga/2004/12/section/227)).
Relief-at-source contributions are not deducted from that income. Under
s. 192(4) they raise the basic and higher rate limits instead, but only for
someone whose income other than savings and dividends would otherwise be
taxed at the higher or additional rate (for a Scottish taxpayer, at a
Scottish rate above the basic rate); s. 227(4C) then applies the raised
limits to the charge, and the excess itself does not count towards that test
(s. 227(5)). So an employee on £45,000 who pays £20,000 gross into a personal
pension, with £50,000 of employer contributions, pays a £2,946 charge on the
£10,000 excess in 2025-26: the excess sits on top of £32,430 of income after
the personal allowance, which is below the £37,700 basic rate limit, so the
limits are not raised and £4,730 of the excess falls in the higher rate
band. Paid through a net pay arrangement, the same contributions would be
deducted first and the charge would be £2,000. HMRC's
[PTM056120](https://www.gov.uk/hmrc-internal-manuals/pensions-tax-manual/ptm056120)
describes the limits as raised by any relief-at-source contribution, without
the s. 192(4) condition, and says the charge is the same whichever way the
contribution is paid; on that reading this charge would also be £2,000. The
model follows the statutory condition.
The amount tested against the allowance is
`pension_contributions_for_annual_allowance`, which counts member
contributions made before age 75, employer contributions and salary
sacrifice ([Finance Act 2004 s. 233](https://www.legislation.gov.uk/ukpga/2004/12/section/233)).
For example, an employee on £100,000 who pays £70,000 into a personal pension
in 2025-26 gets £70,000 of relief and a £2,000 charge on the £10,000 excess,
which falls in the basic rate band. The model's default estimate of unused
allowance for this person is nil, since the estimated input in each earlier
year also exceeds that year's allowance; with £10,000 of unused allowance
brought forward, there is no charge. By default the pension input amount is
cash contributions: `defined_benefit_pension_share` defaults to nil, which
treats every contribution as money purchase. To count defined-benefit
accrual, supply `defined_benefit_pension_input_amount` (for example from a
pension savings statement) together with `defined_benefit_pension_share`, the
share of workplace contributions it replaces; without the share it is added
on top of contributions that still count as money purchase. A share supplied
alone leaves the total unchanged before age 75, since the input amount is
then estimated as those contributions times
`gov.simulation.pensions.defined_benefit_input_per_contribution` (1).
Supplying `pension_contributions_for_annual_allowance` overrides the whole
total.

Relieved contributions also reduce `adjusted_net_income`, so they restore
personal allowance lost above £100,000, as in law
([Income Tax Act 2007 s. 58](https://www.legislation.gov.uk/ukpga/2007/3/section/58)).
An employee on £110,000 has a £7,570 personal allowance in 2025-26, and the
full £12,570 if they pay £10,000 gross into a personal pension.

So the headline behaviour is: **up to the relief limit, pension
contributions reduce taxable income £1-for-£1**. The income-tax saving
that the model reports is the contribution × the person's marginal
rate, plus any personal allowance restored.

## Worked examples

The four scenarios reported in #704 (all self-employed, no other income),
re-run for 2025-26 for a single person aged 40 with contributions entered as
`personal_pension_contributions`; #704 gives no year or age. The "model"
column was re-run in October 2026 on policyengine-uk 2.148.2:

| ID    | Self-employed income | Pension contribution | Total relief as an income-tax change | What the model returns | Why |
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

1. **Relief at source (RAS)**: the pension provider claims the
   basic-rate portion (20%) directly from HMRC. The contributor pays
   from net income and the pension grows by the gross amount. For a
   basic-rate taxpayer, this is the *entire* relief.
2. **Higher-rate top-up**: for taxpayers at higher or additional
   rates, the extra relief (in England, Wales and Northern Ireland, 20%
   for higher rate and 25% for additional rate) is claimed through Self
   Assessment or directly from HMRC. The mechanism is technically a
   **rate-band extension**: the basic rate limit and the higher rate
   limit are both raised by the gross contribution
   ([Finance Act 2004 s. 192(4)](https://www.legislation.gov.uk/ukpga/2004/12/section/192)),
   pushing income that would otherwise be taxed at the higher or
   additional rate down a band.

PolicyEngine computes the **total** relief (both mechanisms together) as a
reduction in income tax, because it operates on annual aggregates rather
than walking the cash-flow steps. It gives less than the law where
basic-rate relief at source is worth more than the tax the deduction saves:
on contributions above the person's taxable income, such as the £720 on a
non-taxpayer's £3,600 contribution, and on contributions that come off
income taxed below 20%, such as dividends at the dividend ordinary rate or a
Scottish taxpayer's starter rate band. The provider still claims 20% in those
cases (s. 192(1)-(3)), but the model has less or no tax to reduce. Otherwise
this matches HMRC's published
statistics on the *fiscal cost of pension tax relief*, which also report the
total across both mechanisms.

If you want to see the user-visible tax bill reduction separately from
the pension-provider's RAS claim, you'd need to split the existing
relief into two output variables (a basic-rate-portion and a
higher-rate-top-up portion). This is a presentation question rather
than a calculation question: the totals are unchanged.

## Marginal tax rate display

#704 also reported a 0% marginal tax rate where 20% or 40% was
expected. The model's `marginal_tax_rate` variable
([`variables/household/marginal_tax_rate.py`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/household/marginal_tax_rate.py))
raises the `employment_income` of each of the household's two eldest adults
in turn (`gov.simulation.marginal_tax_rate_adults`) by
`gov.simulation.marginal_tax_rate_delta` (£1,000, or 0.1% of employment
income where that is larger) and measures the share of the rise that
does not reach `household_net_income`. Re-run in October 2026, it returns
20% for both £30,000 cases and 40% for both £60,000 cases, so the 0%
reported in #704 no longer reproduces in the model.

## References

- HMRC, [Tax on your private pension contributions: Tax relief](https://www.gov.uk/tax-on-your-private-pension/pension-tax-relief): user-facing guide to relief at source and higher-rate relief.
- [Finance Act 2004 s. 188-194](https://www.legislation.gov.uk/ukpga/2004/12/section/188): primary statute for relief at source.
- [Finance Act 2004 s. 227](https://www.legislation.gov.uk/ukpga/2004/12/section/227): annual allowance excess charge.
- HMRC, [Personal pensions statistics](https://www.gov.uk/government/collections/personal-pensions-statistics): including the published cost of pension tax relief.
- [Finance Act 2004 s. 190](https://www.legislation.gov.uk/ukpga/2004/12/section/190) and [s. 191(7)](https://www.legislation.gov.uk/ukpga/2004/12/section/191): the earnings-or-£3,600 limit on relief, with the £3,600 basic amount for relief at source only.
- Model variables: [`pension_contributions_relief`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/hmrc/pensions/pension_contributions_relief.py) and [`personal_pension_contributions_tax`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/hmrc/pensions/private_pension_contributions_tax.py).
