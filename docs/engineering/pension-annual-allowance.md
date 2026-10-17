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
Both annual-allowance income tests use
[`annual_allowance_net_income`](../../policyengine_uk/utils/pensions.py).
This shared helper reconstructs the model's net-income convention from actual
income, before separately modeled pension relief, excluding the NICs-only
salary-sacrifice return. Accordingly:

- `pension_annual_allowance_adjusted_income` adds the total pension input
  amount to that reconstructed income, then subtracts the individual's actual
  own contributions. The helper retains the s. 228ZA(4)(c) net-pay relief
  add-back after limiting trading losses to income remaining after net pay.
  Employer contributions and salary sacrifice are included. Relievable RAS
  contributions made before age 75 do not
  reduce adjusted income.
- `pension_annual_allowance_threshold_income` starts from the same
  reconstructed income, deducts pension relief recomputed on actual earnings
  and contributions, then adds back relevant salary sacrifice. The relief
  deduction combines the net-pay employment-income deduction under
  [FA 2004 s. 193(2)](https://www.legislation.gov.uk/ukpga/2004/12/section/193)
  and the gross RAS deduction
  under s. 228ZA(5)(c).
- Both measures exclude `pension_annual_allowance_taxable_lump_sum_death_benefits`.
  This input must already be included in income elsewhere, such as private
  pension income; it does not itself add income to the taxable base.

Current-year trading-loss relief is income-dependent: the helper rebuilds
adjusted total income and the [ITA 2007 s. 24A relief
cap](https://www.legislation.gov.uk/ukpga/2007/3/section/24A) from actual earnings
and member contributions, including the add-back for trading losses brought
forward. It then limits [s. 64 loss
relief](https://www.legislation.gov.uk/ukpga/2007/3/section/64) to that cap and
the actual income available after relievable net-pay contributions, within
the earnings relief limit and before age 75. Section 193(2) takes net-pay
contributions out of employment income itself; only the excess under
s. 193(4) or (6) is a Step 2 deduction.
[ITA 2007 s. 25(4)](https://www.legislation.gov.uk/ukpga/2007/3/section/25)
prevents Step 2 relief from exceeding the remaining income. This limit
applies in every model year, including before the NICs cap begins in 2029.
It can therefore change pre-2029 allowances for people whose trading-loss
relief is limited by income and who make relievable net-pay contributions.
Removing synthetic pay after deducting the
original relief would retain relief calculated on income the person did not
receive. Threshold income also recomputes [FA 2004 ss. 188–191 pension
relief](https://www.legislation.gov.uk/ukpga/2004/12/section/188) on actual
earnings and contributions.

An explicitly supplied `adjusted_net_income` is authoritative. For this input
path, the helper restores gross Gift Aid and pension relief recomputed on
actual contributions and earnings. It does not remove returned pay or
reconstruct trading-loss relief: the supplied ANI contains neither synthetic
pay nor relief recalculated by the NICs reclassification. The annual-allowance
base is therefore independent of the NICs cap on this path too.

Other modeled deductions do not depend on the returned pay: brought-forward
trade losses, capital allowances and the trading allowance depend on trading
profits. Property finance-cost relief is a downstream tax reducer. Gift Aid's
adjusted-net-income deduction and rate-limit extension do not reduce either
annual-allowance income measure. When ANI is supplied, the helper restores
those ANI deductions, including the separate ITA 2007 s. 58 pension
deduction. Charitable investment gifts and
`other_deductions` remain in `allowances`; their statutory Step 2 treatment is
an existing gap shared with adjusted net income.

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
used by both the taper and the charge. The default DC input includes member
contributions made before age 75, employer contributions and full actual
salary sacrifice. Under [s. 233](https://www.legislation.gov.uk/ukpga/2004/12/section/233)
and [s. 188(3)(a)](https://www.legislation.gov.uk/ukpga/2004/12/section/188),
member contributions made at 75 or over are excluded; employer contributions
still count. The model reads age on **6 October** for the whole year. In the
year of a 75th birthday, member payments are therefore included or excluded
for the whole year according to age on that date; payments are not split at
the birthday. Contributions before 75 that exceed the earnings relief limit
still count. Adjusted income subtracts all actual member contributions under
s. 228ZA(4)(d)(ii), including those excluded from the post-75 DC input.
For defined-benefit
arrangements, supply the statutory total pension input amount, including
valued DB accrual, through this variable. Cash employer funding is not a
valuation of DB rights. Survey estimates retain the existing cash proxy;
this correction does not reconstruct DB rights, overseas adjustments, unused
allowance histories or anti-avoidance arrangements under s. 228ZB.

[The NICs Act 2026](https://www.legislation.gov.uk/ukpga/2026/15/enacted)
changes NICs treatment without changing s. 228ZA. From 2029, the model moves
sacrifice above the NICs exemption cap into
employee contributions and employment income. The AA calculations remove
that synthetic return from both pay and member contributions and recompute
income-dependent relief as described above. Pension relief preserves the
basic RAS amount even when cash earnings are below £3,600 and gives no member
relief from age 75. The DC input keeps the full employer sacrifice at every
age. The threshold-income add-back uses the full
sacrifice before this reclassification. The separate employer-cost wage
response can still change income; it is held fixed when testing the cap's
statutory effect.

Cap invariance covers the two taper incomes, pension input and allowance.
Charge comparisons additionally hold ordinary income-tax inputs fixed: the
separate ANI and personal-allowance interaction can change the marginal tax
charged on the same excess. Ordinary income tax retains its existing
reclassification behavior; [#2454](https://github.com/PolicyEngine/policyengine-uk/issues/2454)
tracks that separate defect.

The taxable death-benefit and grandfathered-sacrifice inputs default to zero.
Pension relief retains the model's aggregate earnings cap and allocation
conventions. Historical years use calendar-year proxies for the named tax
years; the 2015 transitional pension-input alignment rules are outside this
taper calculation.
