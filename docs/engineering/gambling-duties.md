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
periods or loss carry-forward. They floor each input at zero, so a negative
input gives no duty and does not offset another base.
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
| `machine_games_standard_rate_net_takings` | 20%, except the part below | The machine does not qualify for the lower rate, and every dutiable game costs at most £5. |
| `machine_games_standard_rate_higher_stake_net_takings` | 20% to 31 March 2027, then 25% | The part of the standard-rate input from machines with a maximum charge to play above £1 or a maximum prize above £100. |
| `machine_games_higher_rate_net_takings` | 25% | Other dutiable machines. |

Classify the entire machine using all dutiable games it offers. Exactly £5 per
play remains within the standard-rate limit. A gambling category, one selected
game or a premises type does not identify the tax class. The model introduces
no average rate, machine-count weighting or premises allocation. A reform
targeting betting shops needs a separate evidenced allocation of each tax
class's net takings by premises.

Sources: [Finance Act 2012, Schedule 24](https://www.legislation.gov.uk/ukpga/2012/14/schedule/24)
and [HMRC Notice 452](https://www.gov.uk/guidance/machine-games-duty-excise-notice-452).

### Higher-stake machines from 1 April 2027

Budget 2026 moves machines with a maximum charge to play of more than £1, or
a maximum prize of more than £100, from the standard rate of 20% to the higher
rate of 25% from 1 April 2027. Finance Bill 2026-27 will amend the stake and
prize thresholds that set each machine's type, and with it the rate
([OOTLAR paragraph 1.50](https://www.gov.uk/government/publications/budget-2026-overview-of-tax-legislation-and-rates-ootlar/budget-2026-overview-of-tax-legislation-and-rates-ootlar)).
Today, Finance Act 2012 Schedule 24 paragraph 5(3) puts every machine outside
the lower-rate class with a highest charge of at most £5 in the standard-rate
type. From 1 April 2027, such a machine stays at the standard rate only if its
maximum charge is at most £1 and its maximum prize at most £100: a machine at
exactly £1 and £100 stays at 20%, while £1 with a £500 prize, or £2 with a
£100 prize, moves to 25%.

`machine_games_standard_rate_higher_stake_net_takings` is a subset of
`machine_games_standard_rate_net_takings`, not a separate amount:

- The standard-rate input keeps its meaning: takings from every machine with a
  highest charge of at most £5 outside the lower-rate class. A dataset without
  the new input gives the duty before Budget 2026 in every year.
- HMRC's standard-rate liabilities for periods before 1 April 2027 include the
  higher-stake machines, so a provider that builds the standard-rate input
  from them needs no change. From that date HMRC reports those machines at the
  higher rate. A provider that builds the inputs from later liabilities must
  add their takings back to the standard-rate input and leave them out of the
  higher-rate input. Take £100 of remaining standard-rate takings and £100 of
  higher-stake takings: the duty comes to £45. A provider that leaves the £100
  out of the higher-rate input but doesn't add it back gets £25; one that does
  neither gets £50.
- A data provider supplies the higher-stake share of that base, for example
  from the Gambling Commission's machine yield by category. The class
  corresponds closely to Category B, whose limits ([B1: £5 stakes; B2, B3 and
  B3A: £2 and £500; B4: £2 and £400](https://www.gamblingcommission.gov.uk/licensees-and-businesses/guide/gaming-machine-categories))
  exceed one of the thresholds. Category C (£1 and £100) and Category D stay
  within them. The tax class turns on the highest charge and prize a machine
  actually offers, so a category split approximates it.
- The duty floors the new input at zero and caps it at the standard-rate input.
  It never taxes takings that the standard-rate input leaves out.

Within the 6 April to 5 April model year, the change splits by day, as
paragraph 6(6) (a machine that changes type) and paragraph 9(4) (a rate that
changes) require within an accounting period. Model year 2026 charges the
higher-stake part at 25% for 5 of its 365 days, 1 to 5 April 2027; model year
2027 and later charge all of it at 25%. For £1,000 of standard-rate takings,
£400 of them higher-stake, the duty rises from £200 to £200.27 in 2026 and to
£220 from 2027.

The dated switch
`gov.hmrc.gambling_duty.machine_games.higher_stake_machines_at_higher_rate`
turns on from 1 April 2027. Set it to false for the counterfactual without the
change, or move its date to delay it. It shares fiscal-year segments with the
rates, so a rate reform applies to the higher-stake part at whichever rate the
switch selects.

The policy costing puts the measure at £135 million in 2027-28 and £130
million a year to 2031-32
([Budget 2026 policy costings, page 67](https://assets.publishing.service.gov.uk/media/6ae1883fe4367e5c8b0467df/AB26_Policy_Costing.pdf#page=67)).
That costing grows its base with the OBR's Machine Games Duty forecast and nets
off a behavioural response: an elasticity of -0.95, a quarter of lost stakes
moving to Remote Gaming Duty, general attrition and lower Corporation Tax. The
model applies the rates statically to supplied takings and reproduces none of
those responses.

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

The bands have not changed since 1 April 2022:
[HMRC's rates page](https://www.gov.uk/government/publications/rates-and-allowance-excise-duty-gambling-duty/excise-duty-gambling-duty-rates)
gives the same bands for accounting periods beginning on or after 1 April
2026. The government froze them for 2026-27, "with the usual RPI uprating
thereafter" ([OBR November 2025 Economic and Fiscal Outlook, paragraph 3.39](https://obr.uk/docs/dlm_uploads/OBR_Economic_and_fiscal_outlook_November_2025.pdf#page=85)).
Bands for accounting periods from 1 April 2027 are therefore expected to
change but are not yet law, and the catalogue does not anticipate them. The
programme registry's `verified_end_year: 2027` is deliberate: household
outputs use the proxy, not the bands.

Changing the operator catalogue alone leaves the household proxy unchanged.
Scoring a casino band reform requires operator yield distributions and an
incidence mapping, or an explicitly supplied alternative effective fraction.
The fixed proxy does not model behaviour, predict later effective rates or
certify national receipts.

Sources: [Finance Act 1997, sections 10 and 11](https://www.legislation.gov.uk/ukpga/1997/16/section/11/2024-04-06),
[HMRC Notice 453](https://www.gov.uk/guidance/gaming-duty-excise-notice-453),
[HMRC July 2026 tables](https://assets.publishing.service.gov.uk/media/6ab54fd9fe72ed1e2b02f06b/2026_Jul_Bet_and_Gam_Tab.ods)
and [Gambling Commission 2024/25 industry statistics](https://www.gamblingcommission.gov.uk/statistics-and-research/publication/industry-statistics-annual-report-financial-year-april-2024-to-march-2025).

## Projection

Each input declares its duty's index,
`gov.economic_assumptions.indices.obr.gambling_duty_bases.<duty>`, and
dataset projection grows it by the same duty's series in `yoy_growth.yaml`
(`policyengine_uk/data/uprating_indices.yaml`). A series grows the duty's
base, not its receipts: each year's receipts, less the Budget measures they
include, divided by the rate the model charges that year. The model then
applies its own rate changes once. Grown with receipts instead, the base
would carry Remote Gaming Duty's rise to 40% and the formula would charge
40% on it again.

| Fiscal year | Receipts | Source |
| --- | --- | --- |
| 2024-25 | Base year (index 1) | HMRC July 2026 Betting and Gaming tables, `Table_1_BG_receipts` row 45 |
| 2025-26 | Outturn | The same table, row 46 |
| 2026-27 to 2031-32 | Forecast | OBR October 2026 Economic and Fiscal Outlook, receipts Table 4.10, "Betting and gaming duties forecast breakdown" |
| 2032-33 on | None | The `average_earnings` long-run path, as for the other receipts series |

`policyengine_uk/utils/import_obr_forecasts.py` writes the series from
`RECEIPTS_SERIES_SPECS`. It reads each rate from the model's parameter file
and averages it over the OBR's April-to-March year by days. Each duty's rate
comes out as follows:

- **Remote Gaming Duty**: 21% to 31 March 2026, 40% from 1 April 2026.
  Receipts grow 108.3% into 2026-27 (£2,752.0 million against HMRC's
  £1,321.0 million); the base grows (2,752.0 / 40%) / (1,321.0 / 21%) − 1 =
  9.38%.
- **General Betting Duty**: the remote part, 45.5% of the 2024-25 base, goes
  from 15% to 25% on 1 April 2027, so the rate on the whole base goes from
  15% to 15% + 10% × 45.5% = 19.55%. Receipts grow 33.8% into 2027-28
  (£655.6 million to £877.4 million); the base grows (877.4 / 19.55%) /
  (655.6 / 15%) − 1 = 2.70%. The shares come from Microcosm's split of
  HMRC's 2024-25 receipts by the Gambling Commission's 2024-25 gross
  gambling yield, held fixed in every year. That split counts all remote
  horse racing as UK horse racing, which keeps 15%, so the part at 25% may
  be larger, and the 2.70% then overstates the base's growth. Microcosm's
  split gives spread betting no part, so it has no weight.
- **Machine Games Duty**: the three rates do not change, but from 1 April
  2027 the model charges the higher-stake part of the standard-rate base at
  the higher rate (see [higher-stake machines](#higher-stake-machines-from-1-april-2027)).
  Table 4.10's line includes that increase to machine gaming rates, which
  "increases receipts by a further estimated £0.1 billion a year from
  2027-28" (EFO paragraph 4.45). The forecast incorporates every measure
  since March (paragraph 3.2), and the OBR's policy Table 1.1 gives this one,
  with the move of liability to machine suppliers from April 2028, as
  measure 56: £144.2 million of betting receipts in 2027-28, then £162.3,
  £157.6, £155.9 and £156.4 million. The series takes those receipts off.
  The line grows 22.1% into 2027-28; the base grows (826.9 − 144.2) / 677.1
  − 1 = 0.84%. Those receipts also hold the supplier measure's yield, which
  the base therefore excludes. The rate costing also moves a quarter of the
  stakes lost from machines to remote gaming. If measure 56's betting
  receipts count that Remote Gaming Duty and Table 4.10 puts it in the
  remote gaming line, taking the whole measure off this line understates
  the base by that amount. Table 1.1 gives only the measure's head,
  Betting, and Table 4.10 carries no note on it.
  The result is the base before the measure, without the costing's
  behavioural response. The model charges its higher-stake part 25% once,
  and the higher-stake input takes the same index as the standard-rate
  input it belongs to.
- **Gaming Duty**: the household formula charges one effective rate, which
  does not change, so the base grows with receipts. The statutory bands do
  not enter: any change in the duty's effective rate that the OBR's
  forecast includes stays in the base.
- **Bingo Duty**: 10% until its abolition on 1 April 2026. With a zero rate
  there is no base, so the index holds its 2025-26 level from 2026-27.
  Current-law receipts are zero whatever the base; a reform that charges
  Bingo Duty again charges that 2025-26 base in cash terms.
- **Lottery Duty** (12%) and **Pool Betting Duty** (15%): one rate each, so
  the base grows with receipts.

The series rest on these approximations:

- HMRC's receipts are cash. Table 4.10 is on an accrued basis: its totals
  equal the "Betting and gaming taxes" row of the October 2026 Table 4.1,
  whose note says all its taxes are accrued. Growth into 2026-27 compares
  accrued 2026-27 receipts with cash 2025-26 receipts.
- Model years run from 6 April and the OBR's from 1 April. A model year
  that takes in five days of a 1 April rate change charges them at the new
  rate, so FY2025 Remote Gaming Duty (1.2%) and FY2026 General Betting Duty
  (0.4%) sit slightly above the published receipts, and FY2025 Bingo Duty
  (1.4%) slightly below.
- Two lines fall where no rate changes. Table 4.10's Lottery Duty for
  2026-27, £830.5 million, is 15.3% below HMRC's 2025-26 outturn of £980.1
  million. The March 2026 Table 3.10 forecast £1,008.6 million for the same
  year; the October policy table holds no Lottery Duty measure, and the EFO
  gives no reason in paragraph 4.45. Pool Betting Duty
  receipts fall from £8.1 million in 2024-25 to £4.0 million in 2025-26 and
  a forecast £2.8 million in 2026-27, so its index falls by 65%.

Every input in the gambling folder declares an index, including
`machine_games_standard_rate_higher_stake_net_takings`;
`policyengine_uk/tests/test_gambling_duty_base_projection.py` fails for a new
input that declares none.

Sources: [OBR October 2026 Economic and Fiscal Outlook](https://obr.uk/efo/economic-and-fiscal-outlook-october-2026/)
(receipts Table 4.10 and policy Table 1.1, in the
[detailed forecast tables zip file](https://obr.uk/download/october-2026-economic-and-fiscal-outlook-detailed-forecast-tables-zip-file/);
receipts workbook SHA-256
`d115705716d77b11c190385d41cb1924f30080c9331a8a386c04d4e65a368e95`),
[HMRC July 2026 Betting and Gaming tables](https://assets.publishing.service.gov.uk/media/6ab54fd9fe72ed1e2b02f06b/2026_Jul_Bet_and_Gam_Tab.ods),
[Autumn Budget 2026 policy costings, pages 67 and 68](https://assets.publishing.service.gov.uk/media/6ae1883fe4367e5c8b0467df/AB26_Policy_Costing.pdf#page=67)
and [Microcosm's 2024-25 gambling bases](https://github.com/PolicyEngine/microcosm/blob/main/docs/evidence/uk-excise-quantities-1359/outputs/national_reconciliation.json).

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

The reconciliation target is HMRC's UK receipts for April 2024 to March 2025,
the year of the casino proxy:

| Duty | 2024-25 receipts | Cell |
| --- | ---: | --- |
| General Betting Duty | £713.858 million | `B45` |
| Pool Betting Duty | £8.125 million | `C45` |
| Remote Gaming Duty | £1,162.539 million | `F45` |
| Machine Games Duty | £609.245 million | `I45` |
| Gaming Duty | £165.397 million | `E45` |
| Bingo Duty | £25.233 million | `H45` |
| Lottery Duty | £931.887 million | `J45` |
| Total | £3,616.284 million | `K45` |

The cells are in `Table_1_BG_receipts` of the
[HMRC July 2026 tables](https://assets.publishing.service.gov.uk/media/6ab54fd9fe72ed1e2b02f06b/2026_Jul_Bet_and_Gam_Tab.ods),
the file the casino proxy cites, reported in £000. The commentary on HMRC's
[statistics page](https://www.gov.uk/government/statistics/uk-betting-and-gaming-statistics)
gives the same General Betting Duty, Pool Betting Duty and Lottery Duty
figures, rounded. These are cash receipts for a 1 April to 31 March year, so a
reconciliation must handle the timing, period and coverage differences
described for the casino proxy.

The machine tax-class bases cannot score a betting-shop-only reform
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
