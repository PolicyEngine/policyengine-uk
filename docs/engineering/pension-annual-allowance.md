# Pension annual allowance taper

[FA 2004 s. 228ZA](https://www.legislation.gov.uk/ukpga/2004/12/section/228ZA)
requires both adjusted income and threshold income to exceed their limits.
The threshold-income limit is the adjusted-income limit minus the standard
annual allowance. The reduction rounds down to a whole pound before it is
subtracted from the standard allowance, subject to the tapered minimum.

| Tax years | Adjusted-income limit | Threshold-income limit | Minimum allowance |
| --- | ---: | ---: | ---: |
| 2016–17 to 2019–20 | £150,000 | £110,000 | £10,000 |
| 2020–21 to 2022–23 | £240,000 | £200,000 | £4,000 |
| From 2023–24 | £260,000 | £200,000 | £10,000 |

The taper starts in 2016–17 under [Finance (No. 2) Act 2015, Schedule 4,
paragraph 10](https://www.legislation.gov.uk/ukpga/2015/33/schedule/4/paragraph/10).
[Finance Act 2020 s. 22](https://www.legislation.gov.uk/ukpga/2020/14/section/22)
and [Finance (No. 2) Act 2023 s. 22](https://www.legislation.gov.uk/ukpga/2023/30/section/22)
set the later limits. The original reduction multiplier is the standard
allowance less £10,000, divided by £60,000: one half with the statutory
£40,000 standard. From 2020–21 the multiplier is expressly one half.

## Model income conventions

The model's `net_income` includes income before pension relief; that relief
is deducted separately through `allowances`. Employee contributions represent
net pay and personal contributions represent gross relief at source (RAS).
Accordingly:

- `pension_annual_allowance_adjusted_income` adds the total pension input
  amount to `net_income`, then subtracts the individual's own contributions.
  This restores net-pay relief once and includes employer contributions and
  salary sacrifice. RAS contributions do not reduce adjusted income.
- `pension_annual_allowance_threshold_income` subtracts
  `pension_contributions_relief` from `net_income`, then adds back relevant
  salary sacrifice. The relief deduction combines the net-pay deduction
  already present in statutory Step 2 income and the gross RAS deduction
  under s. 228ZA(5)(c).
- Both measures exclude `pension_annual_allowance_taxable_lump_sum_death_benefits`.
  This input must already be included in income elsewhere, such as private
  pension income; it does not itself add income to the taxable base.

Gift Aid's adjusted-net-income deduction does not enter either measure.
These calculations therefore use `net_income`, independently of the separate
ITA 2007 s. 58 pension deduction from adjusted net income.

## Inputs and data limits

Arrangements made on or after **9 July 2015** are relevant salary sacrifice
under s. 228ZA(6). The default treats actual salary sacrifice as relevant
because the survey does not record arrangement dates. Supply
`pension_contributions_via_salary_sacrifice_pre_2015` for the part attributable
to earlier arrangements. Its exclusion is limited to full salary sacrifice
before the NICs exemption cap: that cap does not limit the s. 228ZA add-back.
Flexible remuneration not
represented by these contribution inputs needs an explicit threshold-income
override.

`pension_contributions_for_annual_allowance` is the shared pension input amount
used by both the taper and the charge. It defaults to employee, personal,
employer and actual salary-sacrifice contributions. For defined-benefit
arrangements, supply the statutory total pension input amount, including
valued DB accrual, through this variable. Cash employer funding is not a
valuation of DB rights. Survey estimates retain the existing cash proxy;
this correction does not reconstruct DB rights, overseas adjustments, unused
allowance histories or anti-avoidance arrangements under s. 228ZB.

[The NICs Act 2026](https://www.legislation.gov.uk/ukpga/2026/15/enacted)
changes NICs treatment without changing s. 228ZA. From 2029, the model moves
sacrifice above the NICs exemption cap into
employee contributions and employment income. The pension input amount adds
only the remaining capped sacrifice to those employee contributions, so the
full amount is counted once. The threshold-income add-back uses the full
sacrifice before this reclassification. The separate employer-cost wage
response can still change income; it is held fixed when testing the cap's
statutory effect.

The taxable death-benefit and grandfathered-sacrifice inputs default to zero.
Pension relief retains the model's aggregate earnings cap and allocation
conventions. Historical years use calendar-year proxies for the named tax
years; the 2015 transitional pension-input alignment rules are outside this
taper calculation.
