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
| How relief is given | Reduces taxable income by the contribution (`pension_contributions_relief`) | Treats contributions as paid net of basic rate: grosses them up by 1/(1 − basic rate) and widens every rate band above the starting band by the gross amount, as under relief at source |
| Contributions that get relief | The person's own contributions | Employee contributions, additional voluntary contributions **and employer contributions** |
| Basic-rate relief added to the pot | Not shown separately | Recorded separately (`pension_relief_at_source`) |
| Earnings limit | Relief capped at employment plus self-employment income | No earnings cap; £3,600 limit when total income is below it |
| Annual allowance | £60,000, tapered on adjusted net income above £260,000 (`pension_annual_allowance`) | Tapered on total income above a threshold-income parameter |
| Contributions above the allowance | Charged at the marginal rate (`personal_pension_contributions_tax`) | Relief stops at the allowance; no separate charge |
| Employer contributions in the data | Read from the data (`employer_pension_contributions`) | Imputed when missing from the FRS, using the ONS ASHE employer-contribution bands (`src/Pensions.jl`) |
| Carry-forward of unused allowance | Not modelled | Not modelled |

## Where the two models differ

### 1. Reducing taxable income versus widening the bands

For an income-tax payer whose contribution stays inside one band, the two
methods give the same total relief. They can differ when the person pays
little or no income tax: STBM still records the basic-rate addition to the
pot, which PolicyEngine UK does not show.

**Shared gap: the personal allowance taper.** In law, gross pension
contributions reduce adjusted net income
([Income Tax Act 2007 s. 58](https://www.legislation.gov.uk/ukpga/2007/3/section/58)),
so contributing can restore personal allowance lost above £100,000.
Neither model does this. In PolicyEngine UK, `adjusted_net_income` adds up
the taxable income components without deducting `pension_contributions_relief`:
an employee on £110,000 has adjusted net income of £110,000 and a personal
allowance of £7,570 in 2025-26 whether or not they contribute £10,000.
STBM widens the bands but leaves the taper income unchanged, and its code
flags this as unchecked.

### 2. Employer contributions

STBM counts employer contributions in the relief calculation. In UK law
employer contributions are not taxed as the employee's income, so they get
no personal relief. They are simply outside taxable pay, which is how
PolicyEngine UK treats them. Including them in STBM's relief widens the
employee's bands further than the law does.

### 3. Annual allowance taper

The legal taper uses "adjusted income", which adds employer contributions,
and applies only when "threshold income" is also above £200,000.

- PolicyEngine UK tapers on adjusted net income, with no threshold-income
  test.
- STBM tapers on total income above a threshold parameter.

Neither follows the statute exactly. Both affect only very high earners.

### 4. Lifetime and lump sum allowances

The lifetime allowance was abolished from 6 April 2024 and replaced by the
lump sum allowance and the lump sum and death benefit allowance.
PolicyEngine UK has no parameters for any of these. They apply when pensions
are drawn, not to contributions.

## What neither model does

- Carry-forward of unused annual allowance from the previous three years.
- Behavioural responses: contributions are held fixed when tax rates change.
- Decumulation: crystallisation, the tax-free lump sum, and annuity versus
  drawdown choices.

## References

- STBM source: [`IncomeTaxCalculations.jl`][stbm-it] and [`Pensions.jl`][stbm-pen] at `f534ca1`.
- [STBM blog: pension contributions][stbm-blog].
- PolicyEngine UK: [pension tax relief](./pension-tax-relief.md); variables [`pension_contributions_relief`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/hmrc/pensions/pension_contributions_relief.py), [`pension_annual_allowance`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/hmrc/income_tax/allowances/pension_annual_allowance.py) and [`personal_pension_contributions_tax`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/hmrc/pensions/private_pension_contributions_tax.py).
- HMRC, [Pensions Tax Manual: annual allowance taper](https://www.gov.uk/hmrc-internal-manuals/pensions-tax-manual/ptm057100).
- Issue: [#672](https://github.com/PolicyEngine/policyengine-uk/issues/672).

[stbm]: https://github.com/grahamstark/ScottishTaxBenefitModel.jl
[stbm-it]: https://github.com/grahamstark/ScottishTaxBenefitModel.jl/blob/f534ca1277260a6b4f24c9ab5ebfe9c015e1484d/src/IncomeTaxCalculations.jl
[stbm-pen]: https://github.com/grahamstark/ScottishTaxBenefitModel.jl/blob/f534ca1277260a6b4f24c9ab5ebfe9c015e1484d/src/Pensions.jl
[stbm-blog]: https://stb-blog.virtual-worlds.scot/articles/2022/01/01/pension-contributions.html
