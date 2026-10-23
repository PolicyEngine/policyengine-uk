# Pension treatment compared with the Scottish Tax-Benefit Model

This page compares how PolicyEngine UK and the
[Scottish Tax-Benefit Model (STBM)][stbm] treat personal pension
contributions in income tax, for
[#672](https://github.com/PolicyEngine/policyengine-uk/issues/672) (still open,
October 2026).

The STBM column is taken from its source code at commit
[`f534ca1`][stbm-it] (`src/IncomeTaxCalculations.jl`,
`calculate_pension_taxation!`, and `src/Pensions.jl`). The
[STBM blog post on pension contributions][stbm-blog] that #672 links to is a
short note, and its author says they are unsure of it. It does not describe
the method, so this page does not rely on it.

[How PolicyEngine UK models pension tax relief](./pension-tax-relief.md) has
more detail on the PolicyEngine side.

## Summary

| | PolicyEngine UK | STBM |
|---|---|---|
| How relief is given | Reduces taxable income by the contribution (`pension_contributions_relief`) | Treats contributions as paid net of basic rate: grosses them up by 1/(1 − basic rate) and raises the basic-rate limit and every higher rate limit by the gross amount, as under relief at source |
| Contributions that get relief | The person's own contributions | Employee contributions, additional voluntary contributions **and employer contributions** |
| Basic-rate relief added to the pot | Not shown separately | Recorded separately (`pension_relief_at_source`) |
| Earnings limit | Relief capped at relevant UK earnings (employment income, employer-paid Statutory Sick Pay and Statutory Maternity Pay, and self-employment profit), or £3,600 for relief-at-source contributions if earnings are lower | No earnings cap; when total income is below a basic-amount parameter the limit is that amount (£10,000 in its 2023-24 to 2026-27 systems, £3,600 before) |
| Annual allowance | £60,000 (`pension_annual_allowance`), tapered only when adjusted income is above £260,000 and threshold income is above £200,000, as in FA 2004 s. 228ZA | Tapered on total income above a threshold-income parameter |
| Contributions above the allowance | Annual allowance charge on the excess, taxed as the top slice of income (`personal_pension_contributions_tax`) | Relief stops at the allowance; no separate charge |
| Employer contributions in the data | An input (`employer_pension_contributions`). Microcosm UK draws it from the ONS ASHE employer-contribution bands (Table P10); the Enhanced FRS sets it to three times employee contributions | Imputed when missing from the FRS, using the ONS ASHE employer-contribution bands (`src/Pensions.jl`) |
| Carry-forward of unused allowance | `unused_pension_annual_allowance` (FA 2004 s. 228A) adds to the allowance. As the survey data has no past pension input amounts, from 2020-21 the default estimates it from an assumed five-year history (this year's input and taper incomes deflated by average earnings growth); before 2020-21 it is nil | Not modelled |

The STBM column describes its Scottish systems, its default. In its
rest-of-UK systems from 2023-24, `non_savings_basic_rate` points at the 40%
rate (`params/sys_2023_24_ruk.jl` onwards, marked `FIXME`), so there the
gross-up uses 40% and only the additional-rate limit rises.

## Where the two models differ

### 1. Reducing taxable income versus widening the bands

For an income-tax payer whose contribution stays inside one band above the
Scottish starter rate, the two methods give the same total relief. They can differ when the person pays
little or no income tax: STBM still records the basic-rate addition to the
pot, which PolicyEngine UK does not show.

**The personal allowance taper.** In law, gross pension contributions
reduce adjusted net income
([Income Tax Act 2007 s. 58](https://www.legislation.gov.uk/ukpga/2007/3/section/58)),
so contributing can restore personal allowance lost above £100,000.
PolicyEngine UK does this: `adjusted_net_income` deducts
`pension_contributions_relief`, so an employee on £110,000 has a personal
allowance of £7,570 in 2025-26, and the full £12,570 if they pay £10,000
gross into a personal pension. STBM widens the bands but leaves the taper
income unchanged, and its code flags this as unchecked.

### 2. Employer contributions

STBM counts employer contributions in the relief calculation. In UK law
employer contributions are not taxed as the employee's income, so they get
no personal relief. They are simply outside taxable pay, which is how
PolicyEngine UK treats them. Including them in STBM's relief widens the
employee's bands further than the law does.

### 3. Annual allowance taper

The legal taper
([FA 2004 s. 228ZA](https://www.legislation.gov.uk/ukpga/2004/12/section/228ZA))
uses "adjusted income", which adds employer contributions, and applies only
when "threshold income" is also above £200,000 (from 2020-21).

- PolicyEngine UK applies both tests
  (`pension_annual_allowance_adjusted_income` and
  `pension_annual_allowance_threshold_income`). An employee on £300,000
  who pays £100,000 gross into a personal pension in 2025-26 has adjusted
  income of £300,000 but threshold income of £200,000, so keeps the full
  £60,000 allowance. Its limits: by default the pension input amount is
  cash contributions, so defined-benefit accrual is counted only if supplied
  as an input, and salary sacrifice is treated as made on or after
  9 July 2015 unless `pension_contributions_via_salary_sacrifice_pre_2015` is
  supplied.
- STBM tapers on total income above a threshold parameter.

Both affect only very high earners.

PolicyEngine UK does not model the money purchase annual allowance, the
£10,000 limit on money purchase savings after pensions are first flexibly
accessed
([FA 2004 s. 227ZA](https://www.legislation.gov.uk/ukpga/2004/12/section/227ZA)).
Its annual allowance charge is always on the default chargeable amount,
the pension input amount above the annual allowance (s. 227ZA(3)), never the
alternative chargeable amount that applies once the money purchase annual
allowance is exceeded.

### 4. Lifetime and lump sum allowances

The lifetime allowance was abolished from 6 April 2024 and replaced by the
lump sum allowance and the lump sum and death benefit allowance.
PolicyEngine UK has no parameters for any of these. They apply when pensions
are drawn, not to contributions.

## What neither model does

- Working out carry-forward of unused annual allowance from the previous
  three years' actual pension input. PolicyEngine UK accepts it as an input
  and otherwise estimates it from an assumed history, not from recorded past
  years.
- Behavioural responses: contributions are held fixed when tax rates change.
- Decumulation: crystallisation, the tax-free lump sum, and annuity versus
  drawdown choices.

## References

- STBM source: [`IncomeTaxCalculations.jl`][stbm-it] and [`Pensions.jl`][stbm-pen] at `f534ca1`.
- [STBM blog: pension contributions][stbm-blog].
- PolicyEngine UK: [pension tax relief](./pension-tax-relief.md); variables [`pension_contributions_relief`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/hmrc/pensions/pension_contributions_relief.py), [`pension_annual_allowance`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/hmrc/income_tax/allowances/pension_annual_allowance.py) and [`personal_pension_contributions_tax`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/hmrc/pensions/private_pension_contributions_tax.py).
- [Finance Act 2004 s. 228ZA](https://www.legislation.gov.uk/ukpga/2004/12/section/228ZA) (taper) and [s. 228A](https://www.legislation.gov.uk/ukpga/2004/12/section/228A) (carry-forward).
- HMRC, [Pensions Tax Manual: annual allowance taper](https://www.gov.uk/hmrc-internal-manuals/pensions-tax-manual/ptm057100).
- Issue: [#672](https://github.com/PolicyEngine/policyengine-uk/issues/672).

[stbm]: https://github.com/grahamstark/ScottishTaxBenefitModel.jl
[stbm-it]: https://github.com/grahamstark/ScottishTaxBenefitModel.jl/blob/f534ca1277260a6b4f24c9ab5ebfe9c015e1484d/src/IncomeTaxCalculations.jl
[stbm-pen]: https://github.com/grahamstark/ScottishTaxBenefitModel.jl/blob/f534ca1277260a6b4f24c9ab5ebfe9c015e1484d/src/Pensions.jl
[stbm-blog]: https://stb-blog.virtual-worlds.scot/articles/2022/01/01/pension-contributions.html
