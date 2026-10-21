# Bus fares from journeys

The model prices supplied person-level local-bus journeys from 2024 onwards.
`person_bus_fare_spending` sums London and other-local-bus spending;
`bus_fare_spending` sums it across household members. These outputs describe
spending. `transport_consumption` already includes bus spending, so consumers
must not add it to the consumption total again. This implementation does not
change transport consumption, disposable income or government subsidy totals.

## Inputs and fallback

The Microcosm `nts_bus_travel` stage supplies `bus_in_london_trips`,
`other_local_bus_trips`, their sum `local_bus_trips`, `bus_pass_eligible` and
`local_bus_single_fare_share` at Person level. Trips are annual quantities.
A supplied zero counts as journey data. A cached default does not. If only
`local_bus_trips` is supplied, London residents' trips use the London series
and other residents' trips use the other-local-bus series. When either split
series is supplied, that split takes precedence and the absent series is zero.
Supply consistent splits for cross-boundary travel.

The model treats a person flagged `bus_pass_eligible` as travelling free,
matching Microcosm's pricing assumption. The dataset owns that eligibility
flag; the model does not infer concessionary eligibility from age or change
it when a concessionary scheme is reformed. Supply `bus_pass_eligible` alongside
journey inputs, including in household calculators; an omitted flag defaults to
false and the person pays fares even if eligible for a statutory concession.
For fare-paying passengers,
`local_bus_single_fare_share` is the share of boardings bought as singles,
bounded to [0, 1]. Its fallback is 0.70, the 2024 NTS other-local-bus estimate.
An optional `local_bus_uncapped_single_fare` replaces the table of uncapped
single fares described below for that person. Negative quantities and fares
price at zero.

On loading a UK `Simulation`, a supplied household `bus_fare_spending` moves
to `bus_fare_spending_reported`. The stored total therefore cannot freeze the
journey formula in a reform. Without journey inputs, the model retains this
reported total and allocates it using `fare_allocation_weight_by_age`.
Reported totals retain CPI uprating. Wales and unknown regions retain the
reported total even when journey inputs exist, following Microcosm's decision
to leave areas without published receipts unpriced. Before 2024 the model
also uses this legacy route. Direct core/YAML tests can still override the
household output explicitly.

## Published price benchmark

Microcosm prices journeys using FY2024–25 published facts. The model uses the
same inputs. For each area, receipts `R`, boardings `B`, concessionary
boardings `C`, annual trips per resident `T` and population `P` give:

- Fare-paying yield per boarding: `y = R / (B - C)`.
- Boardings per resident trip: `k = B / (T * P)`.

| Area | R (£) | B | C | T | P | y (£) | k |
|---|---:|---:|---:|---:|---:|---:|---:|
| London | 1,347,434,943.01459 | 1,821,485,000 | 497,523,765.08908 | 13.1155774642333 | 58,620,101 | 1.017729905895 | 2.369144880275 |
| England outside London | 2,069,953,713.42079 | 1,850,509,887.26131 | 519,107,608.59444 | 28.0685543170643 | 58,620,101 | 1.554716967657 | 1.124669202640 |
| Scotland | 391,000,000 | 334,000,000 | 183,599,374.01433 | 28.0685543170643 | 5,546,900 | 2.599723222144 | 2.145240985363 |
| Northern Ireland | 150,082,817.49 | 67,794,551.35 | 8,960,000 | 28.0685543170643 | 1,927,855 | 2.550929922065 | 1.252853758464 |

Sources: [DfT BUS01 and BUS05i](https://www.gov.uk/government/statistical-data-sets/bus-statistics-data-tables),
[NTS0705a](https://www.gov.uk/government/statistical-data-sets/nts07-car-ownership-and-access),
[Scottish Transport Statistics 2025, tables 2.2a and 2.8](https://www.transport.gov.scot/publication/scottish-transport-statistics-2025/chapter-2-bus-and-coach-travel/),
[NI Public Transport Statistics 2024–25, figures 3, 4 and 6](https://www.infrastructure-ni.gov.uk/publications/public-transport-statistics-northern-ireland-2024-25),
and [Microcosm's fact extraction and pricing implementation](https://github.com/PolicyEngine/microcosm/pull/954).
Population denominators use ONS mid-2024 estimates. London uses all English
residents because non-residents also travel there. Scotland and Northern
Ireland use the English other-local-bus trip rate as a proxy, as Microcosm does.
These translations include interchanges and differences between operator
boardings and resident trips; they are not counts of legs for a known trip.
`gov.dft.bus.benchmark_year` (2024) names the fiscal year these facts describe.

## Fares by year

In other years each area's yield moves with its published fares index:

```
yield(t) = benchmark_yield * index(t) / index(benchmark_year)
```

`gov.dft.bus.local_bus_fares_index` holds DfT's
[BUS0415a](https://www.gov.uk/government/statistical-data-sets/bus04-costs-fares-and-revenue)
quarter-end values (March 2005 = 100) for London, England outside London and
Scotland, from DfT's June 2026 release (quarters to March 2026;
[archived copy](https://web.archive.org/web/20260619124752/https://assets.publishing.service.gov.uk/media/6a310ac715f2a70fac7e6006/bus0415.ods)),
the vintage Chronicle and Microcosm vendor. DfT's September 2026 release, now
served at the same address, revises the last two quarters and adds June 2026;
move to it together with Microcosm. Each value is dated at the start of the
quarter it ends, and `fiscal_year_blend` day-weights the quarters over 6 April
to 5 April, the model's year. FY2024–25 outside London is therefore
(86 × 181.6 + 92 × 185.7 + 92 × 185.9 + 90 × 206.4 + 5 × 210.5) / 365 = 190.23,
within 0.2% of the mean of its four quarter ends (189.9). After the last
published quarter the index grows with the OBR consumer price index each
January, as `private_rent_index` does. Northern Ireland has no published index,
so its yield grows with CPI from the benchmark year. Wales stays unpriced.

The CPI projection also raises the fares in the index that the £3 cap holds at
£3, while the cap term below measures changes from a nominal £3. From January
2027 a ticket held at a cap therefore costs about £3 times the CPI growth since
March 2026 more than the cap allows. That overstates the outside-London yield
by 0.4% in 2027–28 and 0.8% in 2028–29, about 0.3 points more each year after.
A cap reform is measured against the same reference as the baseline, so its
cost does not move.

| Area | FY2024–25 | FY2025–26 | FY2026–27 | FY2027–28 |
|---|---:|---:|---:|---:|
| London | 196.10 | 196.10 | 197.13 | 201.08 |
| England outside London | 190.23 | 214.18 | 219.09 | 223.48 |
| Scotland | 210.63 | 229.94 | 235.90 | 240.63 |

FY2025–26 and earlier are published; later years are CPI projections. The
index records prices paid, so it already contains each cap in force while it
is published, including the rise to £3 in January 2025 (outside London 185.9
in December 2024, 206.4 in March 2025). The cap term below adds only what the
index cannot contain.

Each area follows its own index, so the England total moves with the
receipts-weighted mix of the London and outside-London indices: +7.6% in
FY2025–26. DfT's England index rose 6.4%. Its step from December 2024 to
March 2025 was 5.6%, against 11.0% outside London and none in London, so it
weights outside London at about one half, where receipts weight it at 61%.
A receipts target moved by the England index therefore sits below the model's
England total.

## Caps and the uncapped counterfactual

`gov.dft.bus.fares.cap` records the national cap on participating single-ticket
services in England outside London: £2 from January 2023, £3 from January 2025,
and £2 from January through December 2027. After December 2027 it is infinite,
representing the end of the announced scheme. These dates follow the
[DfT evaluation](https://www.gov.uk/government/publications/evaluation-of-the-2-bus-fare-cap),
[£3 scheme guidance](https://www.gov.uk/guidance/3-national-bus-fare-cap) and
[2027 announcement](https://www.gov.uk/government/speeches/2-bus-fares-from-january-2027).
The cap does not affect the London series, Scottish or Northern Irish fares.
England outside London uses a representative participating-service assumption;
route-level participation and local lower caps require caller-supplied fares.
The table of uncapped fares below is fitted to national figures and applied
the same way in every English region outside London. Where a combined authority
already runs its own lower single fare, a national cap reform therefore
overstates the savings, and elsewhere it understates them. National totals
hold, but regional and distributional splits of a cap reform lean the wrong way.

The published yield and index already include ticket discounts and the cap in
force. `gov.dft.bus.reference_fares.cap` records that cap: the cap in force up
to the last published quarter of the index (£3 from January 2025), held after
it. For an English fare-paying person's other-local-bus boardings, the model
uses:

```
yield(t) = max(0, benchmark_yield * index(t) / index(benchmark_year)
                  + single_share * sum over bands b of share_b *
                    (annual_min(fare_b, fares.cap, t) -
                     annual_min(fare_b, reference_fares.cap, t)))
spending = trips * boardings_per_trip * yield(t)
```

Both schedules are read in the same year. While the index is published they
agree and the cap term is zero, so the baseline is the published path. After
the last published quarter the term adds the scheduled changes: the £2 cap from
January 2027 and its end in 2028. A reform of `fares.cap` adds its own
difference from the reference. Leave `reference_fares` unchanged in reforms.
When a newly published quarter is added to the index, extend
`reference_fares.cap` with the cap then in force;
`policyengine_uk/tests/test_bus_fare_parameters.py` fails until the two
schedules agree up to the last published quarter.

`annual_min` caps the fare in each date interval, then weights the intervals
from 6 April to 5 April, assuming uniform journeys through the year. It does
not cap a fare using the average cap. Both `fares` and `reference_fares` keep
calendar dates (their index files propagate `preserve_calendar_dates` to the
cap leaves), so a cap change part-way through a year applies from its date.
The source receipts use 1 April to 31 March; this approximation treats them as
the corresponding model year's benchmark. Annual Scenario changes apply to the
full model fiscal year.

### Uncapped single fares

What a cap saves depends on how uncapped single fares are spread, not on their
average. `gov.dft.bus.uncapped_single_fares` holds three bands, each with its
share of single tickets and its mean uncapped fare at FY2024–25 prices:

| Band | Share | Mean fare |
|---|---:|---:|
| `LOW`, at or below £2 | 0.55 | £1.65 |
| `MIDDLE`, above £2 and up to £3 | 0.30 | £2.21 |
| `HIGH`, above £3 | 0.15 | £3.87 |

The fares rise with the OBR CPI after FY2024–25 and the shares stay, so a fixed
cap saves more as fares rise. The model caps each band's mean fare under both
schedules and weights the bands by their shares, which must sum to one. With
the bands at their means, the table is exact for caps of £2 and £3 at
FY2024–25 prices and approximate for other caps; a cap below the low band's
mean needs more bands.

`scripts/fit_bus_cap_savings.py` fits the table by least squares to the facts
below, each scaled by its tolerance. It searches shares in steps of one point
and fares in steps of one penny, keeps each band's mean at least 10% above its
lower edge, and sets the low band's fare so all singles average £2.15:

| Fact | Source | Target | Table gives |
|---|---|---:|---:|
| A full year at £2, 2023–24 | Fare cap support, DfT BUS05bi | £278.95m ± 10% | £280.9m |
| Part of the December 2024 to March 2025 index step outside London due to the £3 cap | BUS0415a: +11.0%; neighbouring quarters 0.1% to 2.3% | 10% ± 1 point of the yield | 9.8% |
| The £3 cap in 2025 | ["over £150 million"](https://www.gov.uk/government/speeches/national-bus-fare-cap) | £150m ± 20% | £140.0m |
| The £2 cap in 2027, against no cap | ["£400 million"](https://www.gov.uk/government/speeches/2-bus-fares-from-january-2027) | £400m ± 20% | £411.6m |
| Mean pre-cap price of single tickets | [DfT evaluation](https://www.gov.uk/government/publications/evaluation-of-the-2-bus-fare-cap), Table 6 | £2.15 ± £0.10 | £2.15 |
| Share of single tickets above £2 | Table 6: £0.32 / (£2.73 − £2.00) | 0.44 ± 0.05 | 0.45 |
| Their mean pre-cap price | Table 6 | £2.73 ± £0.10 | £2.76 |
| 2024–25: £2 for 270 days, then £3 | Fare cap support, DfT BUS05bi | £515.69m, not fitted | £268.5m |

The £400 million is read as £2 against no cap: the £3 scheme is funded only to
December 2026, and the £2 scheme replaces it. Read as £2 against a continued
£3 cap, the table gives £247.3m, 38% below. The script prints both.

The 2024–25 grant, for the benchmark year itself, is reported and not fitted;
the table puts it at about half. Grant per fare-paying boarding rose 78% on
2023–24, while the outside-London index rose 6.7%, receipts per fare-paying
boarding rose 2.8%, and the cap rose only for the last quarter. The figure may
therefore hold more than that year's forgone fares (timing or coverage of
payments, not checked). The 2023–24 grant and the two announced figures all
put a full year at £2 near £0.3bn, not £0.6bn. The single £2.748 fare this
table replaced was calibrated to the 2024–25 grant.

The costs use the 0.70 default single share and fare-paying boardings outside
London (BUS01 journeys less BUS01c concessionary journeys: 1,281m in 2023–24
and 1,331m in 2024–25, which also stands for 2025 and 2027), with fares moved
to each year by CPI. Table 6 compares January to October 2022 with the same
months of 2023 and is read at face value, for the table's shape. Deflated to
2022 prices it would put the 2023–24 saving about a third above the grant.
Possible reasons, not checked, are that the grant pays operators for revenue
lost net of the journeys the cap added, and that Table 6 covers the larger
participating operators only. The two announced figures are budgets; the £2
cap's first ten months paid £210m against £245m planned. The table is a fitted
central estimate, not an observed fare distribution.

At FY2025–26 prices the table saves £0.39 per single ticket for a full year at
£2 against no cap, and £0.15 at £3: about £0.36bn and £0.14bn a year at
2024–25 boardings. The single £2.748 fare this replaced saved £0.75 at £2
(about £0.70bn) and nothing at £3.

A dataset or calculator can supply `local_bus_uncapped_single_fare` for each
person. Where it is supplied, that person's single tickets cost that one fare
before the cap, and the table is not used. Single-year datasets extended by
`Simulation` uprate it with CPI. Very large reductions can reach the zero-yield
floor.

## Other reform controls and limits

`fare_index / prior_law_fare_index` multiplies both journey-priced and legacy
spending. Both default to one; they are neutral reform controls rather than
historical index series. Keep the denominator positive. `ridership_index`
defaults to one and multiplies journey-priced spending, leaving supplied
journey inputs intact. The model includes no demand elasticity or automatic
ridership growth. Trip translations stay constant after 2024 unless changed
explicitly; yields move with the fares index. Dataset CPI-uprated household
bus totals do not determine prices where journeys are available.

A proportional scenario can set `gov.dft.bus.fare_index` to 0.9 for a 10%
reduction. A cap scenario changes `gov.dft.bus.fares.cap`; leave the reference
schedule and benchmark yield unchanged. Set the cap to infinity to remove it.
The fixture-scale tests exercise both routes through UK dataset loading and
Scenario, including baseline isolation and the January cap transitions.
