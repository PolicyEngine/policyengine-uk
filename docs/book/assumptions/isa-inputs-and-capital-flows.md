# ISA income, capital and account flows

## Income inputs

Household situations use additive income inputs. `savings_interest_income`
means ordinary interest outside tax-free accounts, before tax. ISA interest
belongs in `individual_savings_account_interest_income`, and ISA dividends or
distributions belong in `individual_savings_account_dividend_income`. Ordinary
`dividend_income` excludes those ISA distributions. ISA gains do not belong in
`capital_gains`.

`tax_free_savings_income` defaults to ISA interest. An explicitly supplied
aggregate, including zero, overrides that default. Market income, capital
income and HBAI income add this exempt-interest aggregate once. They do not
also add its ISA component. For example, £2,000 ordinary interest, £500 ISA
interest and £300 ISA dividends produce £2,800 market returns and £2,000
taxable savings interest before allowances. The £500 does not offset interest
from an unrelated taxable account. [ISA Regulations regulation 22](https://www.legislation.gov.uk/uksi/1998/1870/regulation/22)
provides the income-tax exemption.

The supported dataset loaders also accept older gross-interest datasets.
Their adapter subtracts effective exempt interest from gross savings interest
before calculation, preserves explicit exempt-interest overrides, and records
the input and projection conventions. See the dataset-source engineering
guide for the versioned metadata contract. A raw household situation has the
additive convention; it has no dataset provenance to identify older gross
amounts. Producers must mark newly additive datasets before switching their
exports. The model must not infer the convention from account amounts. Local
council-tax reduction non-dependant tests that use normal gross income add
ordinary and exempt returns together, preserving their gross-income bands.
Income-tax and Tax Credit income bases exclude the separately supplied ISA
returns; their input definitions do not turn a tax exemption into a general
exclusion from every means test.

PolicyEngine-UK maintainers retain responsibility for this compatibility
adapter, including its integration with private PolicyEngine Core input and
formula APIs. Changes to Core require checking the ISA contract regressions
for legacy and additive datasets, explicit overrides, projections and resets.
Retiring the adapter requires an explicit maintainer decision supported by a
versioned producer and consumer migration.

`non_cash_isa_cash_interest` is an **of-which** component of total ISA interest,
covering cash interest and corresponding alternative-finance returns in a
stocks-and-shares or innovative finance ISA. If only this detail is supplied,
it supplies the ISA-interest total; an explicit total takes priority. A
supplied total must include the detail. The detail is never added to market
income a second time.

For household inputs carried into later years, ISA dividends use the same
nominal GDP-per-capita index as ordinary `dividend_income`.
`non_cash_isa_cash_interest` uses the same ONS household-interest-income index
as ordinary `savings_interest_income`. An explicit observation for a later
year takes priority and provides the starting amount for subsequent years.
Dataset projections grow stored ISA dividends and non-cash ISA cash interest
by nominal GDP per capita, matching the dataset rules for ordinary dividends
and savings interest. This also applies before 2031. The non-cash interest
detail therefore follows the existing dataset interest rule, while direct
household inputs use the ONS index above. Alignment of the interest indices
is tracked separately in [#2638](https://github.com/PolicyEngine/policyengine-uk/pull/2638).
The legacy and additive interest contracts retain their recorded conventions.

From 6 April 2027, `isa_cash_interest_flat_rate_charge` applies the savings
basic rate to that detail, without personal allowances or the personal
savings allowance. The manager's final charge enters `gov_tax`,
`household_tax` and HBAI income deductions separately from `income_tax`.
The gross interest enters market income once. [SI 2026/1018 regulations 1
and 15](https://www.legislation.gov.uk/uksi/2026/1018/made) establish this
charge; [Finance Act 2026 section 5](https://www.legislation.gov.uk/ukpga/2026/11/section/5)
sets the 2027–28 savings basic rate at 22%.

## Winter Fuel Payment and projections

From fiscal 2025, the model calculates gross Winter Fuel Payment entitlement
separately from the personal income-tax charge. The charge recovers the full
payment when the recipient's total taxable income exceeds £35,000, subject
to the relevant-benefit exemption. ISA interest and distributions are exempt
income and stay outside that total. The gross payment itself also stays
outside taxable income. These treatments follow [HMRC's Winter Fuel Payment
charge guidance](https://www.gov.uk/hmrc-internal-manuals/paye-manual/paye130030)
and [the ISA tax exemption](https://www.gov.uk/individual-savings-accounts/how-isas-work).

The £35,000 threshold is fixed in nominal terms in the model. Growth in
taxable income can therefore move recipients across it. Dataset projections
extend through 2032; where a growth series ends in 2030, the extension repeats
its final annual growth rate in 2031 and 2032. The dataset-source and economic
assumptions documentation describe these conventions. This extension is an
extrapolation rather than a new published forecast.

These mechanisms alone do not establish the cause or magnitude of a
population trend. A comparison must distinguish gross payments from the
income-tax charge and use the same dataset, policy version, year and income
convention. Earlier model versions represented recovery through a household
eligibility proxy, so results from that version require a separate comparison
with the current personal charge. No current population attribution is
established by the household tests.

## Capital stocks

`cash_isa` is a household stock separate from `savings`. It sums the members'
`cash_isa_balance`, and `stocks_and_shares_isa` sums their
`stocks_and_shares_isa_balance`, as `household_lifetime_isa_balance` sums
`lifetime_isa_balance`. A dataset or situation that stores a household total
keeps it: the model sums the person balances only for a year with no stored
total. In each later year the model grows the latest total that a dataset
stores by the index of `savings`, `corporate_wealth` or `lifetime_isa_balance`
respectively, including years after the dataset projection ends, unless the
dataset holds the person balances for a later year than the total, or a reform
changes what the total sums or stops a person balance reading its inputs. A
household input in a situation applies only to its own year; the person
balances carry the variable-level uprating to later years. The means tests read
the household totals, so they pool a person's balance with the household's
other financial capital rather than attribute it to their own benefit unit.

Ordinary accessible cash ISA balances enter the capital sources for Universal
Credit, Housing Benefit, Pension Credit, Income Support, income-based JSA and
income-related ESA. There is no general ISA-wrapper disregard and no generic
10% sale-cost deduction for cash. Existing source-specific disregards,
ownership allocation assumptions and reported-capital overrides still apply. A
complete reported capital amount already includes relevant ISA holdings; it
replaces covered components rather than adding them again.

For example, £5,000 savings and a £3,000 ordinary cash ISA give £8,000 UC
capital. [UC regulation 72](https://www.legislation.gov.uk/uksi/2013/376/regulation/72)
then gives eight £4.35 monthly tariff units, or £34.80 a month. Stocks-and-shares
ISA holdings remain within `share_like_capital`. The separate existing
`lifetime_isa_countable_capital` valuation is unchanged. It does not gain
transaction-level first-home or terminal-illness valuation from the new flow
inputs.

Population estimates depend on the input balances, reported-capital
overrides, benefit take-up and calibrated weights as well as the capital
rules. [Microcosm issue 1360](https://github.com/PolicyEngine/microcosm/issues/1360)
tracks coordinated producer migration and calibration work. A released
producer dataset recalibrated for this expanded capital definition has not
been verified here. The numerical gap between a consistent population
estimate and the relevant DWP outturn also remains unverified. Household
consumer tests establish the routing into benefit calculations; they do not
establish a population magnitude or fit to outturn.

## Lifetime ISA payments and withdrawals

`lifetime_isa_payments` contains qualifying additions in the year, including
qualifying transfers from other ISA types. Exclude growth, government bonuses,
transfers between Lifetime ISAs, returned failed-purchase withdrawals,
defaulted payments and rebated fees. The bonus is 25% of qualifying payments
up to £4,000, from age 18 until before age 50. Payments at ages 40–49 assume a
valid account first funded before age 40. The model does not decide whether
an account may be opened. [ISA Regulations regulations 4ZA and 10A and
Schedule paragraph 1](https://www.legislation.gov.uk/uksi/1998/1870)
define these conditions.

`lifetime_isa_withdrawals` is the gross withdrawal, including any charge,
excluding qualifying transfers between Lifetime ISAs and withdrawals on
death. All such withdrawals are exempt at the charge-free age of 60 or when
`lifetime_isa_terminally_ill` is true. That flag means the investor has a
registered medical practitioner's written evidence of life expectancy below one year;
it is not a generic benefit-eligibility flag.

`lifetime_isa_withdrawals_towards_first_home` is the part paid directly to an
eligible conveyancer towards the purchase price, with required declarations
and completion or return procedures satisfied. It excludes fees and payments
through the investor. The model separately requires:

- the investor's `lifetime_isa_first_time_buyer` flag: no previous residential
  ownership anywhere, irrespective of another joint purchaser's history;
- `lifetime_isa_months_since_first_payment` of at least 12, including qualifying
  transfer continuity;
- a positive whole-property price no greater than £450,000 in
  `main_residential_property_purchased`;
- a UK main-home purchase, represented by
  `main_residential_property_purchased_is_in_uk`;
- qualifying secured finance, represented by
  `main_residential_property_purchased_with_mortgage`. This means an eligible
  legal mortgage or regulated home-purchase plan satisfying the applicable
  connected-lender and buy-to-let restrictions. The qualifying-condition
  input includes the prescribed exceptions for overseas Crown employees
  and their spouses or civil partners, and permitted delayed main-home
  occupation.

Only the bounded qualifying home-payment portion is exempt. The residual
gross withdrawal is charged at 25%, or 20% during the temporary coronavirus
period. These rules come from [Schedule paragraphs 4–7 and 5A](https://www.legislation.gov.uk/uksi/1998/1870/schedule).

From 29 October 2026, a purchase that meets every one of these conditions
except the £450,000 price cap pays 20% on the home payment instead of 25%
(Schedule paragraphs 5 and 6A, inserted by
[SI 2026/1130](https://www.legislation.gov.uk/uksi/2026/1130/made)). The rest
of the withdrawal still pays 25%. `gov.hmrc.isa.lifetime.above_cap_purchase`
holds the rate and its start. Parameters are read on 30 April, so the model
applies the 20% rate from fiscal 2027–28; a withdrawal from 29 October 2026 to
5 April 2027 pays 25% in the model. When such a purchase fails and the money
is returned, the charge is restored to the account (paragraph 10A), so a
returned withdrawal should be left out of the inputs.

The model records `lifetime_isa_bonus` in government spending and
`lifetime_isa_withdrawal_charge` in government revenue. Both are capital
flows, excluded from household current benefits, taxes and net income. The
flows do not automatically update a supplied account balance. This is an
accounting convention for the model's current-income measures.

## Subscription limits

`gov.hmrc.isa.annual_subscription_limit` is the £20,000 limit on a person's
subscriptions in a tax year to all their ISAs other than Junior ISAs
([ISA Regulations regulation 4ZA(1)](https://www.legislation.gov.uk/uksi/1998/1870/regulation/4ZA)).
It was £15,000 from 1 July 2014 and £15,240 from 6 April 2015. The model reads
these limits from 2015–16; 2014–15 and earlier years, with their lower limits
and cash sub-limits, are not modelled.
Cash has had no limit of its own since 1 July 2014, so
`gov.hmrc.isa.cash.subscription_limit` is infinite and cash counts only
towards the annual limit.
[SI 2026/1018 regulation 6](https://www.legislation.gov.uk/uksi/2026/1018/regulation/6/made)
sets a £12,000 cash limit from 6 April 2027 for a person who is 64 or under
at the end of the tax year, but Budget 2026 retains the £20,000 cash limit
for all savers, with secondary legislation to be laid in November 2026
([OOTLAR paragraph 2.5](https://www.gov.uk/government/publications/budget-2026-overview-of-tax-legislation-and-rates-ootlar/budget-2026-overview-of-tax-legislation-and-rates-ootlar)).
Current law here therefore has no cash limit, and the £12,000 is a reform
setting. `gov.hmrc.isa.cash.full_limit_age` (65) is the age at which a cash
limit stops applying. `cash_isa_subscription_limit` reads the age at the end
of the year (5 April) from the date of birth, so a person aged 64 on
6 October whose 65th birthday falls on or before 5 April has the annual limit
for cash.

The inputs are per-person flows in the year: `cash_isa_subscriptions`,
`stocks_and_shares_isa_subscriptions` and the existing
`lifetime_isa_payments`, which `isa_subscriptions` adds up. They sum over
all of a person's accounts of each type, net of current-year subscriptions
withdrawn from a flexible ISA. They exclude transfers between ISAs, interest
and growth, and the subscriptions that
[regulation 5D](https://www.legislation.gov.uk/uksi/1998/1870/regulation/5D)
disregards, such as replacement subscriptions to a flexible ISA, additional
permitted subscriptions, defaulted subscriptions and transfers from a matured
Child Trust Fund
([HMRC guidance](https://www.gov.uk/guidance/manage-isa-subscriptions-for-your-investors)).
`lifetime_isa_payments` includes transfers into a Lifetime ISA from other
ISAs, which count towards the Lifetime ISA limit but are not new
subscriptions for the annual limit, so the total overstates subscriptions
where that input includes them. A withdrawal charge restored under Schedule
paragraph 10A is neither a subscription nor a Lifetime ISA payment (SI
2026/1130 regulations 3 and 4). Innovative finance ISAs are not included.
The inputs are not uprated: growing them would put people who pay in exactly
the annual limit above it in the baseline. Nominal subscriptions grow, so flat
amounts understate how much a lowered limit leaves out in later years. A
producer can grow them instead and cap each person at the limit in force.

The model compares the inputs with the limits in force and does not cap them.
`cash_isa_subscriptions_above_limit` is cash above the person's cash limit,
and `isa_subscriptions_above_limit` is the total above the annual limit. Cash
above both limits counts in both, so the two must not be added. Both are zero
for data that met the limits in force when it was collected. A reform that
lowers a limit reports what it leaves out. For example, a person aged 40
paying £20,000 into cash ISAs in 2027–28 has £8,000 above a £12,000 cash
limit.

The model reports these amounts and no more. It does not say where money
above a limit goes or change any tax for it: the model is static by year and
the data has no ISA history, so it holds no balances moved out of ISAs in
earlier years. A population run gives the first year's amount above a limit;
the tax on money moved out of ISAs over several years rests on the official
costing.

## Annual resolution and coverage

A bare year Y represents the fiscal year from 6 April Y to 5 April Y+1.
Parameters retain their legal effective dates; the annual model samples
rates at 30 April. Fiscal 2020 therefore uses the temporary 20% withdrawal
charge and fiscal 2021 uses 25%. The annual model cannot distinguish a
withdrawal in late March 2020 within fiscal 2019. Likewise, the 20% charge for
a purchase above the price cap has effect for withdrawals from 29 October
2026, but fiscal 2026 samples 30 April 2026. So a 2026–27 run charges 25% on
such a withdrawal made from 29 October 2026 to 5 April 2027 (159 of the
year's 365 days), and the 20% applies from fiscal 2027. Annual ages and purchase
conditions similarly represent the relevant transactions at one annual
status. Multiple transactions with different conditions require externally
prepared qualifying amounts.

Help to Buy ISA bonuses are not modelled here. Junior ISAs, Child Trust
Funds, transfers between ISA types (including the SI 2026/1018 restrictions on
transfers into cash ISAs) and the First Time Buyer ISA announced at Budget
2026 for April 2029 are also outside this implementation. Population data
without payment, withdrawal, subscription or non-cash-interest detail inputs
retain zero for those flows; data without per-person ISA balances keeps its
stored household totals. Household tests establish the rules; population
effects require a separate
certified dataset measurement.
