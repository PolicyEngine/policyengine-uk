# Household gambling duties

The model calculates General Betting Duty, Pool Betting Duty, Remote Gaming
Duty, Machine Games Duty, casino Gaming Duty incidence, Bingo Duty and Lottery
Duty from supplied annual household bases. The `gambling_duty` output adds
these seven components and enters `household_tax` and `gov_tax` once. The
incidence assumption passes all duty to consumers. These inputs support
household calculations; they do not establish population revenue estimates or
repair existing survey data.

## Periods and attribution

Coverage starts in 2024/25. Model period `2024` covers 6 April 2024 to 5 April
2025. The six statutory duty formulas apply dated rates within each interval
of that fiscal year and weight each interval by its share of the year, using
`utils.excise.fiscal_year_segments`. They assume each supplied annual base
accrues uniformly. For example, Finance Act 2026 raises Remote Gaming Duty on
1 April 2026: FY2025 contains 360 days at 21% and five at 40%. The remote
betting change on 1 April 2027 similarly affects five days of FY2026. A reform
dated within a fiscal year is split the same way. The casino incidence proxy
takes one value per model year instead, as described below.

Each input supplies a nonnegative, already-attributed dutiable base in pounds.
All inputs default to zero. A data provider must allocate operator liabilities
to households, preserving statutory netting, adjustments and exemptions before
supplying these bases. A household's raw signed stakes minus winnings do not
satisfy this contract. The formulas do not reproduce operator accounting
periods or loss carry-forward and do not validate negative input values.
Positive inputs before 2024 produce default zero because those model years
remain outside the implemented coverage.

The full pass-through assumption follows the issue's household-incidence
proposal. The OBR's November 2025 forecast assumed around 90% pass-through of
the Budget 2025 increases; that behavioural assumption about changes is not a
baseline incidence fraction in this implementation. This implementation does
not reproduce the OBR's demand or substitution costing. Government receipts
and household incidence use the same attributed base here.

Source: [OBR November 2025 Economic and Fiscal Outlook, paragraph 3.40](https://obr.uk/docs/dlm_uploads/OBR_Economic_and_fiscal_outlook_November_2025.pdf#page=85).

## General Betting Duty

Supply these separate, non-overlapping inputs:

| Annual household input | Dutiable base |
| --- | --- |
| `remote_uk_horseracing_betting_net_losses` | Remote fixed-odds bets wholly related to horse racing in the United Kingdom. |
| `remote_other_betting_net_losses` | Other qualifying remote fixed-odds bets, excluding all pool and spread bets, exchange commission, on-course bets and qualifying licensed-premises self-service betting terminals. |
| `land_based_fixed_odds_betting_net_losses` | Dutiable off-course land-based fixed-odds bets, including qualifying self-service betting terminals in licensed premises. Exclude on-course bets, pools, spread bets and exchange commission. |
| `horse_and_dog_pool_betting_net_losses` | Dutiable pool or totalisator bets wholly related to horse or dog racing. |
| `financial_spread_betting_net_losses` | Dutiable financial spread betting net receipts of UK bookmakers. |
| `other_spread_betting_net_losses` | Dutiable nonfinancial spread betting net receipts of UK bookmakers. |
| `betting_exchange_commission` | Chargeable exchange commission charged to UK persons. Exchange stakes must not enter another input. |

The rate is 15% for fixed odds, racing pools and exchange commission, 3% for
financial spreads and 10% for other spreads. Qualifying other remote
fixed-odds bets use 25% from 1 April 2027. Bets wholly on UK horse racing,
qualifying licensed-premises self-service terminals and pool bets retain their
existing treatment. On-course bets are exempt and must not enter a dutiable
input. A terminal used to bet on future real events differs from a gaming
machine subject to Machine Games Duty.

Sources: [Finance Act 2014, Chapter 1](https://www.legislation.gov.uk/ukpga/2014/26/part/3/chapter/1),
[Finance Act 2026, section 87](https://www.legislation.gov.uk/ukpga/2026/11/section/87)
and [HMRC gambling duty guidance](https://www.gov.uk/guidance/general-betting-duty-pool-betting-duty-and-remote-gaming-duty).

## Pool Betting Duty

Supply `pool_betting_net_receipts`, the household's attributed dutiable pool
betting base, including statutory additions and excluding qualifying
community-benefit bets. The rate is 15%. Exclude fixed-odds bets and pools
wholly related to horse or dog racing; those racing pools enter General Betting
Duty. A mixed pool does not become exempt from Pool Betting Duty merely
because one leg concerns horse or dog racing.

Source: [Finance Act 2014, Chapter 2](https://www.legislation.gov.uk/ukpga/2014/26/part/3/chapter/2).

## Remote Gaming Duty

Supply `remote_gaming_net_losses`, the household's attributed chargeable,
non-exempt remote gaming profits base. The rate is 21% in the starting
coverage, rising to 40% on 1 April 2026. The input excludes gaming already
charged with another gambling tax and other exemptions in section 161. Remote
bingo enters this base only where chargeable: section 161 also exempts UK
licensed bingo and specified unlicensed bingo with mixed remote and in-person
participation. Do not allocate the same gaming to another duty base.

Sources: [Finance Act 2014, sections 154 to 162](https://www.legislation.gov.uk/ukpga/2014/26/part/3/chapter/3),
[Finance Act 2026, section 86](https://www.legislation.gov.uk/ukpga/2026/11/section/86)
and [HMRC historical rates](https://www.gov.uk/government/statistics/uk-betting-and-gaming-statistics/historical-uk-betting-and-gaming-duty-rates).

## Machine Games Duty

Supply attributed dutiable net takings separately:

| Input | Rate | Statutory machine class |
| --- | --- | --- |
| `machine_games_lower_rate_net_takings` | 5% | Every dutiable game costs at most 20p and has a maximum cash prize of at most £10. |
| `machine_games_standard_rate_net_takings` | 20% | The machine does not qualify for the lower rate, and every dutiable game costs at most £5. |
| `machine_games_higher_rate_net_takings` | 25% | Other dutiable machines. |

Classify the entire machine using all dutiable games it offers. Exactly £5 per
play remains within the standard-rate limit. A gambling category, one selected
game or a premises type does not identify the tax class. The model introduces
no average rate, machine-count weighting or premises allocation. A reform
targeting betting shops needs a separate evidenced allocation of each tax
class's net takings by premises.

Sources: [Finance Act 2012, Schedule 24](https://www.legislation.gov.uk/ukpga/2012/14/schedule/24)
and [HMRC Notice 452](https://www.gov.uk/guidance/machine-games-duty-excise-notice-452).

## Bingo Duty

Supply `bingo_net_receipts`, the household's nonnegative share of dutiable
bingo promotion profits after statutory adjustments and exemptions. Bingo Duty
charged 10% before abolition on 1 April 2026. FY2025 therefore charges
£3,600 on a uniform £36,500 attributed base: £100 per day × 360 days × 10%.
FY2026 charges zero. The operator's exemption where duty would be less than
£1 does not create a household threshold. The supplied base must already
reflect the operator's treatment.

Exclude bingo exempt under the pre-repeal law, including wholly remote
unlicensed bingo under section 17(2A). Chargeable remote gaming uses the
separate Remote Gaming Duty contract, including its section 161 exemptions.

Sources: [Betting and Gaming Duties Act 1981, section 17, as at 6 April 2024](https://www.legislation.gov.uk/ukpga/1981/63/section/17/2024-04-06)
and [Finance Act 2026, section 88](https://www.legislation.gov.uk/ukpga/2026/11/section/88).

## Lottery Duty

Supply `national_lottery_ticket_spending`, the chargeable consideration for
National Lottery tickets and scratchcards. The rate is 12%, with no deduction
for winnings or expenses. Section 25 includes amounts paid, given or debited
in connection with the ticket. Where consideration falls below a shown ticket
price, or no consideration is given, use the deemed shown price. Exempt
lotteries and bingo are outside this input. The model's initial parameter
entry marks verified 2024/25 coverage and makes no earlier commencement claim.

Sources: [Finance Act 1993, section 24](https://www.legislation.gov.uk/ukpga/1993/34/section/24/2024-04-06),
[section 25](https://www.legislation.gov.uk/ukpga/1993/34/section/25/2024-04-06)
and [HMRC Notice 458](https://www.gov.uk/guidance/lottery-duty-excise-notice-458).

## Casino Gaming Duty incidence

Supply `land_based_casino_net_losses`, the household's nonnegative attributed
dutiable casino gross gaming yield. The attribution includes applicable gaming
charges, such as participation charges for equal-chance games, alongside
stakes less prizes where the operator acts as banker. Exclude admission-only
charges, machine games and gaming taxed or exempt under the other duties.

The household formula multiplies this base by the empirical assumption
`household.consumption.gambling.casino_effective_rate`, initially **0.235487**
(23.5487%). It holds that fraction constant from model year 2024 onwards.
Like the other household consumption assumptions, the proxy takes one value
per model year: the value in force on 1 January of the year in which the model
year starts. Unlike a change to a statutory rate, a change to the proxy dated
within a fiscal year is not split by day; it applies to a whole model year
when it is in force on that 1 January. The proxy sits outside `gov`, where the
reform routes read a bare year such as `"2027"` as a calendar year, so a day
split would spread such a reform over two model years.

The approved proxy divides these official observations:

| Observation, April 2024 to March 2025 | Amount | Source location |
| --- | ---: | --- |
| HMRC UK Gaming Duty cash receipts | £165.397 million | July 2026 Betting and Gaming tables, `Table_1_BG_receipts!E45`, reported in £000. |
| Gambling Commission GB casino **game** gross gaming yield | £702.36095883367 million | 2024/25 industry statistics, `8a!B94`, also `8!H49`; provisional. |

The exact division gives 0.2354871778104747736771859341. Rounding to six
fractional decimals changes the arithmetic on that denominator by £124.89,
below HMRC's £1,000 source reporting unit. Casino **machine** yield of
£231.47255869591993 million is excluded; machines use Machine Games Duty.
The original HMRC ODS SHA-256 is
`3979df37c0611cce371f80950bacac6bc5e9dad499c726f6138f838c882914e8`;
the original Gambling Commission workbook SHA-256 is
`ea5335233cc728f9c500d4ed3233bd996b60acb2cff11f271e0fcf002c8e1b6b`.

The observations have different coverage. HMRC reports UK cash receipts with
payment and accounting lags; the Gambling Commission reports GB licensed
operator yield and marks the 2024/25 row provisional. Both source periods run
1 April to 31 March, while the model uses 6 April to 5 April. The division
therefore supplies a documented incidence approximation, without establishing
matched geography, taxpayers or accrual periods. Its numerical precision does
not resolve those differences. [Issue 2587](https://github.com/PolicyEngine/policyengine-uk/issues/2587)
tracks review and refresh of the proxy.

Statutory Gaming Duty applies progressive bands to casino premises for an
operator accounting period. The separate
`gov.hmrc.gambling_duty.gaming.normal_six_month_bands` catalogue records the
registered-premises, normal six-month schedule: 15% on the first £2,686,000,
20% on the next £1,852,000, 30% on the next £3,243,000, 40% on the next
£6,845,000 and 50% thereafter. It excludes unregistered-gaming treatment and
alternative accounting-period adjustments. Household annual losses never
enter those bands.

Changing the operator catalogue alone leaves the household proxy unchanged.
Scoring a casino band reform requires operator yield distributions and an
incidence mapping, or an explicitly supplied alternative effective fraction.
The fixed proxy does not model behaviour, predict later effective rates or
certify national receipts.

Sources: [Finance Act 1997, sections 10 and 11](https://www.legislation.gov.uk/ukpga/1997/16/section/11/2024-04-06),
[HMRC Notice 453](https://www.gov.uk/guidance/gaming-duty-excise-notice-453),
[HMRC July 2026 tables](https://assets.publishing.service.gov.uk/media/6ab54fd9fe72ed1e2b02f06b/2026_Jul_Bet_and_Gam_Tab.ods)
and [Gambling Commission 2024/25 industry statistics](https://www.gamblingcommission.gov.uk/statistics-and-research/publication/industry-statistics-annual-report-financial-year-april-2024-to-march-2025).

## Tax totals and fiscal classification

The seven component duties enter `gambling_duty`, which enters household and
government taxes once. The fiscal partition assigns that head to **Other HMRC
taxes**. OBR's November 2025 Economic and Fiscal Outlook, Table A.5 footnote 5,
places betting and gaming duties in that row. The model measures only the
gambling part from supplied bases; residual Other HMRC taxes remain
unmodelled. No Table 3.1 allocation is asserted. Removing the row from the
partition's list of rows with no household measure does not claim complete
coverage of the row.

Source: [OBR November 2025 Economic and Fiscal Outlook, Table A.5](https://obr.uk/docs/dlm_uploads/OBR_Economic_and_fiscal_outlook_November_2025.pdf#page=195).

## Data and coverage follow-ups

Released data need a separate mapping from gambling stakes and winnings to
these dutiable bases. The mapping must distinguish remote and land-based
products, avoid overlap, address survey under-recording and reconcile weighted
totals with HMRC receipts using compatible periods and population coverage.
The formulas make no allocation from `recreation_consumption`. Default-zero
inputs do not demonstrate upstream data adoption or population coverage.

The three machine tax-class bases cannot score a betting-shop-only reform
without joint tax-class-by-premises yield data. Premises shares alone do not
identify that allocation, and machine counts do not provide yield weights.
No assumption of independence between premises and tax class enters the
model. [Issue 2586](https://github.com/PolicyEngine/policyengine-uk/issues/2586)
remains open for that contract and data work, alongside Microcosm 1359 and
Chronos 381. The separate casino review remains under issue 2587.

Gambling removal from the VAT base also requires a comparable expenditure
contract: subtracting net gambling losses from a gross-stakes consumption
aggregate would mix bases. Data adoption, calibrated population receipts and
VAT-base repair remain separate from this seven-family engine foundation.
