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
it when a concessionary scheme is reformed. For fare-paying passengers,
`local_bus_single_fare_share` is the share of boardings bought as singles,
bounded to [0, 1]. Its fallback is 0.70, the 2024 NTS other-local-bus estimate.
An optional `local_bus_uncapped_single_fare` overrides the representative
uncapped fare described below. Negative quantities and fares price at zero.

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

The published yield already includes ticket discounts and the benchmark cap.
For an English fare-paying person's other-local-bus boardings, the model uses:

```
current_yield = max(0, benchmark_yield + single_share *
                   (annual_min(uncapped_fare, current_cap) -
                    annual_min(uncapped_fare, reference_cap)))
spending = trips * boardings_per_trip * current_yield
```

`annual_min` caps the fare in each date interval, then weights the intervals
from 6 April to 5 April, assuming uniform journeys through the year. It does
not cap a fare using the average cap. Both `fares` and `reference_fares` preserve
calendar dates. `reference_year` is 2024 and `reference_fares` holds the benchmark
schedule fixed when the policy cap changes. The source receipts use 1 April to
31 March; this approximation treats them as the corresponding model year's
benchmark. Annual Scenario changes apply to the full model fiscal year.

The default uncapped fare is £2.748019953976. This is an aggregate assumption,
not an observed fare distribution. The FY2024–25 cap grant is £515,693,216.60.
With `F = B - C` outside London and single share `s = 0.70`, the assumption
solves `s * (u - annual_min(u, reference_cap)) = grant / F`. Since `2 < u < 3`,
the reference year has 270 days at £2 and 95 at `u`, giving:

```
u = 2 + grant / (F * 0.70 * 270/365)
```

Removing the cap therefore raises the benchmark yield from about £1.55 to
£1.94 at the representative share, matching the grant-addback calculation
in issue #1871. This assumes full grant pass-through and no demand response.
Individual shares can differ, so a dataset aggregate need not recover the
published grant. Changing the cap above `u` has no further effect with this
representative fare; supply person-specific uncapped fares for other price
assumptions. Very large reductions can reach the zero-yield floor.

## Other reform controls and limits

`fare_index / prior_law_fare_index` multiplies both journey-priced and legacy
spending. Both default to one; they are neutral reform controls rather than
historical index series. Keep the denominator positive. `ridership_index`
defaults to one and multiplies journey-priced spending, leaving supplied
journey inputs intact. The model includes no demand elasticity or automatic
ridership growth. Benchmark yields and trip translations stay nominally
constant after 2024 unless changed explicitly. Dataset CPI-uprated household
bus totals do not determine prices where journeys are available.

A proportional scenario can set `gov.dft.bus.fare_index` to 0.9 for a 10%
reduction. A cap scenario changes `gov.dft.bus.fares.cap`; leave the reference
schedule and benchmark yield unchanged. Set the cap to infinity to remove it.
The fixture-scale tests exercise both routes through UK dataset loading and
Scenario, including baseline isolation and the January cap transitions.
