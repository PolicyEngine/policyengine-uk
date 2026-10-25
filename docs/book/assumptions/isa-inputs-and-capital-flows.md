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
`non_cash_isa_cash_interest` and an ISA-interest total carried forward under
the additive contract use the same index as ordinary `savings_interest_income`:
households' interest received per person
(`ons.per_capita.household_interest_income`, see
[#2638](https://github.com/PolicyEngine/policyengine-uk/pull/2638)). An
explicit observation for a later year takes priority and provides the starting
amount for subsequent years. Dataset projections grow stored ISA dividends by
nominal GDP per capita, as for ordinary dividends, and stored non-cash ISA cash
interest by the per-person interest index, as for ordinary savings interest.
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

`cash_isa` is a household stock separate from `savings`. Ordinary accessible
cash ISA balances enter the capital sources for Universal Credit, Housing
Benefit, Pension Credit, Income Support, income-based JSA and income-related
ESA. There is no general ISA-wrapper disregard and no generic 10% sale-cost
deduction for cash. Existing source-specific disregards, ownership allocation
assumptions and reported-capital overrides still apply. A complete reported
capital amount already includes relevant ISA holdings; it replaces covered
components rather than adding them again.

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

The model records `lifetime_isa_bonus` in government spending and
`lifetime_isa_withdrawal_charge` in government revenue. Both are capital
flows, excluded from household current benefits, taxes and net income. The
flows do not automatically update a supplied account balance. This is an
accounting convention for the model's current-income measures.

## Annual resolution and coverage

A bare year Y represents the fiscal year from 6 April Y to 5 April Y+1.
Parameters retain their legal effective dates; the annual model samples
rates at 30 April. Fiscal 2020 therefore uses the temporary 20% withdrawal
charge and fiscal 2021 uses 25%. The annual model cannot distinguish a
withdrawal in late March 2020 within fiscal 2019. Annual ages and purchase
conditions similarly represent the relevant transactions at one annual
status. Multiple transactions with different conditions require externally
prepared qualifying amounts.

Help to Buy ISA bonuses are not modelled here. Subscription-limit compliance,
Junior ISAs, Child Trust Funds and a proposed First Time Buyer ISA are also
outside this implementation. Population data without payment, withdrawal or
non-cash-interest detail inputs retain zero for those new flows. Household
tests establish the rules; population effects require a separate certified
dataset measurement.
