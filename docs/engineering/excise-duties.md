# Household excise duties

The model calculates alcohol duty, tobacco duty, vehicle excise duty on cars,
and duty on LPG and natural road fuel gas from supplied household inputs.
`household_tax` and `gov_tax` include these amounts once, alongside petrol and
diesel duty. These totals combine the different annual bases described below.
The incidence assumption is full pass-through to consumers.

The model also includes seven gambling duty families from supplied attributed
household bases. [Household gambling duties](gambling-duties.md) documents the
rates, casino incidence proxy, period conventions and outstanding population
data, machine-premises and VAT work.

## Coverage and periods

Alcohol, tobacco and car duty calculations cover 2024/25 to 2026/27. The alcohol
parameter history starts on 1 August 2023; the preceding alcohol regime and a
complete 2023/24 calculation are outside this implementation. Tobacco rates
start on 22 November 2023. The new alcohol, tobacco and car formulas return their
default zero before 2024; that is an unmodelled period, not a statutory exemption.
Gas duty covers 2022/23 onwards and includes the 1 January 2027 and 1 March 2027
increases. SI 2026/555 removed the September 2026 step announced at Budget 2025
and moved the December 2026 step to 1 January 2027. Rates after the last dated
entry stay constant; the gas parameters do not forecast future inflation
increases.

For alcohol and tobacco, a model year such as `2026` represents 6 April 2026 to
5 April 2027. Quantities and cigarette retail prices are constant across that
year. Duty is calculated separately for every rate interval, then weighted by
the interval's share of the year. Tobacco Budget-day changes take effect at
18:00, while the 1 October 2026 change takes effect at midnight. Applying the
cigarette minimum within each interval matters when the minimum begins or ceases
to bind during the year.

These two rate nodes use `preserve_calendar_dates: true` to opt out of the
usual conversion of government parameters to annual values. Their raw parameter
values retain their actual dates; `utils/excise.py` performs the annual
calculation. Value-level `effective_time` metadata records the Budget-day time.
Annual `Scenario.parameter_changes` and bare-year legacy reform dictionaries
apply to a complete UK fiscal year. Explicit date ranges retain the dates the
caller supplies.

The linear fuel duty rates on petrol, diesel and road fuel gases use the
existing `fiscal_year_blend: true` machinery. Each rate is keyed to the date it
takes effect and day-weighted across the model year, 6 April to 5 April. Time
of day is not modelled. Monthly `fuel_duty` allocates one twelfth of each annual
volume and uses the model's annual rate; it does not represent duty on a dated
purchase.

Consequently, `household_tax` and `gov_tax` mix year bases. For model period
`2026`, alcohol, tobacco and fuel duty use 6 April 2026 to 5 April 2027, and VED
uses 1 April 2026 to 31 March 2027. They are added to existing annual components,
including income tax and VAT. Aggregation does not realign or prorate these components
to a common reporting year. The totals therefore do not represent a consistent
January-to-December receipts period. Before comparing `gov_tax` with
calendar-year receipts, align each component to that calendar year; changing the
total's year label alone does not perform that conversion.

## Alcohol inputs

For each of `beer`, `cider`, `sparkling_cider`, `wine`, `spirits`, and
`other_fermented`, supply household inputs:

- `<product>_litres`: litres of the drink bought over the year, default zero.
- `<product>_abv`: strength as a fraction, for example `0.05` for 5%.
- `<product>_draught_share`: the fraction qualifying for statutory draught relief,
  default zero. This should reflect qualifying containers and dispensing, not
  simply where the household drinks the product.

Default strengths are illustrative assumptions in
`household.consumption.alcohol`, not population averages: beer 4%, cider and
sparkling cider 4.5%, wine 12%, spirits 40%, other fermented products 5%.
Override them for a known product. Each product input represents one strength;
where a household buys products spanning multiple rate bands, calculate the
components separately or supply the summed product duty.

The product definitions are the statutory categories. For example, fruit ciders
that do not qualify as cider belong under `other_fermented`. The model covers
Schedule 7 strength bands, Schedule 8 draught rates, the sparkling-cider 5.5%
boundary, and the temporary wine-strength easement ending on 1 February 2025.
Small producer relief and demand responses are excluded.

The result `alcohol_duty` sums the six product-duty outputs. In 2026/27,
100 litres of 5% beer gives £112.90 with no draught relief, or £97.25 when all of
it qualifies for draught relief.

Sources: [HMRC Alcohol Duty rates](https://www.gov.uk/guidance/alcohol-duty-rates)
and [historic rates](https://www.gov.uk/government/statistics/alcohol-bulletin/alcohol-bulletin-historic-duty-rates).

## Tobacco inputs

Supply household `cigarettes_per_week`, `cigarette_price_per_pack`, and any of
`hand_rolling_tobacco_grams_per_week`, `cigars_grams_per_week`,
`other_tobacco_grams_per_week`, and `heated_tobacco_grams_per_week`.
Weekly quantities are annualised with the model's 52-week convention. Prices
refer to twenty cigarettes. The default price uses the ONS 2024 calendar-year
average of £15.85 and stays constant thereafter; supply the actual price when
available. The default is a data assumption, not a tax parameter.

`tobacco_duty` applies the higher of specific-plus-ad-valorem duty and minimum
duty to cigarettes, plus weight-based duty on other products. Specific and
minimum cigarette parameters are stored in pounds **per cigarette**; other
specific rates are pounds per kilogram. Vaping products duty is outside this
implementation.

Sources: [HMRC Tobacco Products Duty rates](https://www.gov.uk/government/publications/rates-and-allowances-excise-duty-tobacco-duty/excise-duty-tobacco-duty-rates)
and [ONS cigarette price series CZMP](https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/czmp/mm23).

## Car inputs

Supply one car for each person who keeps a car:

- `car_first_registration_date`, formatted `YYYY-MM-DD`.
- `car_co2_emissions`, in g/km.
- `car_fuel_type`: `PETROL`, `DIESEL_RDE2`, `DIESEL_NON_RDE2`,
  `ALTERNATIVE_FUEL` (including hybrids and LPG), or `ELECTRIC` (including other
  zero-emission cars).
- `car_list_price`, the original list price before discounts.
- `car_engine_size`, in cc, for cars first registered before 1 March 2001.
- `car_is_ved_exempt`, for an applicable exemption, including an eligible
  historic or disabled person's vehicle.

Without a registration date the result is zero. `num_vehicles` and
`owns_vehicle` do not create a taxable car, since they cannot identify its
schedule. `car_vehicle_excise_duty` computes each person's charge;
`vehicle_excise_duty` aggregates them within the household.

The calculation assumes one twelve-month licence in each VED rate year
(1 April to 31 March), with uninterrupted annual renewals from first
registration. It charges the full first licence in the registration year and
then the annual renewal; it does not spread that first licence across tax
years. It excludes partial-year ownership, refunds, instalment surcharges,
changes of tax class and the 50% disability reduction. A person with more than
one car can supply their combined `car_vehicle_excise_duty` directly.

The schedules cover engine size before March 2001; CO2 bands from March 2001
to March 2017, including the pre-23 March 2006 band-K cap; and first-year and
standard rates from April 2017. The expensive-car supplement applies during
the next five annual licences. Its zero-emission threshold rises to £50,000
from 2026/27, including cars registered in 2025/26; zero-emission cars registered
before April 2025 remain exempt from the supplement. The 2024/25 zero-emission
exemption and alternative-fuel discount are also represented. Vans, motorcycles
and the proposed electric-vehicle mileage charge are outside this implementation.

Sources: [DVLA vehicle tax rate tables](https://www.gov.uk/vehicle-tax-rate-tables),
[Budget 2025 rate tables](https://www.gov.uk/government/publications/budget-2025-overview-of-tax-legislation-and-rates-ootlar/annex-a-rates-and-allowances),
and [zero-emission vehicle guidance](https://www.gov.uk/guidance/vehicle-tax-for-electric-and-low-emissions-vehicles).

## Road fuel gas inputs

Supply annual household `lpg_kg` and `natural_gas_kg`. Natural gas includes
biogas used as road fuel, not domestic heating. The inputs are kilograms,
matching the legislation. No universal litre-to-kilogram density is assumed.
The existing `fuel_duty` output includes these charges. Rural fuel duty relief
continues to apply only to petrol and diesel.

From 1 March 2027 onwards, the gas parameters hold LPG at £0.3161/kg and natural
gas at £0.2470/kg. This implementation stops at the last numerical rates in the
HMRC 2026-to-2027 schedule and does not extrapolate gas rates using an inflation
forecast. This is a modelling limitation: HMRC states that RPI uprating resumes
from 2027/28. The petrol and diesel rate includes forecast RPI uprating each
1 April from 2027, so its rates rise while the gas rates stay flat. Later-year gas duty is therefore lower than it would be
under the same uprating assumption. Analyses beyond March 2027 that require
consistent fuel-duty forecasts must supply an uprated gas-rate path explicitly.

Sources: [HMRC fuel duty rates 2026 to 2027](https://www.gov.uk/government/publications/fuel-duty-rates-for-2026-to-2027/fuel-duty-rates-2026-to-2027)
(RPI uprating from 2027/28),
[HMRC amended fuel duty rates 2026 to 2027](https://www.gov.uk/government/publications/amended-fuel-duty-rates-for-2026-to-2027/amended-fuel-duty-rates-2026-to-2027)
and [SI 2026/164 as amended by SI 2026/555](https://www.legislation.gov.uk/uksi/2026/164).

## Petrol and diesel rate

The main rate on unleaded petrol and diesel is keyed to each statutory change:
52.95p a litre from 23 March 2022, continued by annual orders to 31 December 2026;
55.95p from 1 January 2027 (SI 2026/164 as amended by SI 2026/555); and the Hydrocarbon Oil
Duties Act 1979 rate of 57.95p from 1 March 2027. Budget 2025 states that rates
will be uprated by RPI from April 2027, and HM Treasury's Budget 2025 costing
dates this from 1 April 2027. That uprating is policy, not law: HMRC's amended
note of 22 May 2026 says final rates will be confirmed at Budget 2026. No
official source names the RPI measure. The model applies the previous calendar
year's RPI growth from the OBR forecast in
`gov.economic_assumptions.yoy_growth.obr.rpi` on each 1 April, rounded to the
nearest hundredth of a penny. The steps to 1 April 2031 are written out by
`calculate_fuel_duty_rates.py`, and a test fails when they fall out of date
with the RPI forecast. Later steps come from the parameter's uprating metadata.
The RPI index ends in 2039, so the last step is 1 April 2040.

An annual reform names a model year and replaces the rate for all of it. For
model years to 2030 it leaves other years unchanged. `Scenario.parameter_changes`
reapplies uprating after the change, so an override from model year 2031, where
the steps come from uprating metadata, restarts uprating from the last written
rate: every later year stays one 1 April step behind. Reform classes and legacy
reform dictionaries change the annual values after uprating and are not
affected.

## Projecting alcohol and tobacco quantities

Each alcohol and tobacco quantity input declares its product group's index,
and dataset projection grows it by the same group's series in
`gov.economic_assumptions.yoy_growth.obr.per_capita`
(`policyengine_uk/data/uprating_indices.yaml`). Each series is the growth in
the OBR's clearances of the group per person (#2596):

| Inputs | Series | OBR line |
| --- | --- | --- |
| `cigarettes_per_week` | `tobacco_clearances.cigarettes` | Table 4.11, "Cigarette clearances (million sticks)" |
| `hand_rolling_tobacco_grams_per_week` | `tobacco_clearances.hand_rolling_tobacco` | Table 4.11, "Hand rolled tobacco clearances" |
| `cigars_grams_per_week`, `other_tobacco_grams_per_week`, `heated_tobacco_grams_per_week` | `tobacco_clearances.other_tobacco_products` | Table 4.11, "Other tobacco products" |
| `beer_litres`, `cider_litres`, `sparkling_cider_litres` | `alcohol_clearances.beer_and_cider` | Table 4.12, "Beer and cider" |
| `wine_litres`, `other_fermented_litres` | `alcohol_clearances.wine` | Table 4.12, "Wine", which includes other fermented products |
| `spirits_litres` | `alcohol_clearances.spirits` | Table 4.12, "Spirits", which includes spirit-based ready-to-drinks |

Table 4.11 splits non-cigarette clearances into hand-rolled tobacco and other
tobacco products only, so the cigar, other tobacco and heated tobacco inputs
share one series. The strengths (`<product>_abv`) and draught shares are
ratios, and `cigarette_price_per_pack` is a price, so they keep their values;
a forward path for the cigarette price is a separate change.

### Population

`extend_single_year_dataset` copies the base year's dataset into each later
year, and `apply_single_year_uprating` multiplies each column that
`uprating_indices.yaml` lists by one plus its series' growth in that year.
The file lists `household_weight` under
`gov.economic_assumptions.yoy_growth.ons.population`. So, for household i in
year t, with population growth p(t) and a quantity series g(t):

- the weight is w(i, t) = w(i, t - 1) × (1 + p(t));
- the quantity is q(i, t) = q(i, t - 1) × (1 + g(t));
- the weighted total is Q(t) = Σ w(i, t) × q(i, t) = (1 + p(t)) × (1 + g(t)) × Q(t - 1).

With g(t) = (1 + c(t)) / (1 + p(t)) - 1, where c(t) is the growth in
clearances, Q(t) = (1 + c(t)) × Q(t - 1): the weighted total follows the
clearances. A series of c(t) itself would give
Q(t) = (1 + p(t)) × (1 + c(t)) × Q(t - 1) and count population growth twice.
`ons.population` grows 1.54% from 2024-25 to 2031-32, so totals grown that
way would end 1.54% above the clearances.

For cigarettes in 2025-26, the October 2026 EFO's outturn of 12,224.6 million
sticks against the March 2026 EFO's 2024-25 outturn of 13,578.2 million is a
fall of 9.97%. Population grows 0.33%, so the series holds
12,224.6 / 13,578.2 / 1.0033 - 1 = -10.27% (-0.102653).

### Years

| Model year | Series | Source |
| --- | --- | --- |
| 2024 (2024-25) | Base year: 0, index 1 | The alcohol and tobacco duties start in model year 2024 |
| 2025 | Outturn | October 2026 Tables 4.11 and 4.12 (2025-26) over March 2026 Tables 3.11 and 3.12 (2024-25) |
| 2026 to 2031 | Forecast | October 2026 Tables 4.11 and 4.12 |
| 2032 on | Clearances held flat: 1 / (1 + p(t)) - 1 | As `road_fuel_volume` after the OBR's forecast |

The OBR's years run from 1 April and the model's from 6 April. As for road
fuel, each series stores the fiscal year that starts in year t at t-01-01.
The indices, `gov.economic_assumptions.indices.obr.per_capita.*`, start at 1
in 2024 and stand at:

| Group | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Cigarettes | 0.897 | 0.803 | 0.721 | 0.660 | 0.599 | 0.558 | 0.520 |
| Hand-rolled tobacco | 0.826 | 0.769 | 0.712 | 0.652 | 0.610 | 0.584 | 0.556 |
| Other tobacco products | 0.861 | 0.815 | 0.781 | 0.715 | 0.679 | 0.653 | 0.615 |
| Beer and cider | 0.969 | 0.950 | 0.929 | 0.921 | 0.914 | 0.903 | 0.891 |
| Wine | 0.965 | 0.963 | 0.945 | 0.937 | 0.929 | 0.917 | 0.907 |
| Spirits | 0.984 | 0.974 | 0.956 | 0.950 | 0.944 | 0.933 | 0.924 |

Past `PROJECTION_END_YEAR` (2032), policyengine-core scales each input by
the index it declares.

`policyengine_uk/utils/import_obr_forecasts.py` writes the six series from
`CLEARANCE_SERIES_SPECS` in the same run as the other receipts series (see
the steps for a new EFO in the economic assumptions README). It requires each
table to state its unit, in a row label or a note, and reads `ons.population`
from the `yoy_growth.yaml` it rewrites.

### Budget measures and reforms

The October 2026 forecast incorporates the measures announced at Budget 2026
and since the March forecast (EFO paragraph 3.2). The OBR's policy Table 1.1
holds no change to an alcohol or tobacco duty rate. Three measures reach the
two duties, and none moves either by more than £13 million a year:

- measure 19, more generous Small Producer Relief from 1 February 2027:
  alcohol duty £1.5 million lower in 2026-27 and £9.2 million to £9.9
  million lower a year after (the model leaves out Small Producer Relief);
- measure 45, HMRC's measures to close the tax gap: tobacco duty £0.7
  million higher in 2026-27, rising to £12.7 million in 2031-32, and alcohol
  duty £0.3 million to £4.8 million higher;
- measure 95, the removal of the £135 customs duty relief on low-value
  imports from October 2028: tobacco duty up to £0.8 million and alcohol
  duty up to £0.4 million lower a year.

The forecast still assumes rising duty rates. The OBR expects alcohol
receipts to grow, "driven by increases to the duty rate that offset an
assumed average 1 per cent decline in alcohol consumption in each year"
(paragraph 4.43), and tobacco receipts to fall "as higher duty rates only
partly offset falling consumption" (paragraph 4.44). The clearances carry
that consumption trend under the OBR's own rate path, not a Budget change.

The dataset projection reads no duty rate (`uprating_input_paths` in
`policyengine_uk/data/economic_assumptions.py`), so the indices grow
quantities whatever rates the model charges. A reform to alcohol or tobacco
duty rates therefore moves receipts through the rates alone: the model
applies no consumption response to it. Current law in the model holds the
alcohol rates at their 1 February 2026 values, the tobacco rates at their
1 October 2026 values and the default cigarette price at its 2024 average,
while the OBR's volumes come with the rates it expects.

### Receipts against the OBR's forecast

On quantities that follow the clearances, the model's duty moves with its
own rates. A constructed dataset of one household at weight 1 that holds the
UK's 2024-25 clearances shows the effect. It treats beer and cider as beer
at 4% with no draught relief, wine and other fermented products as wine at
12%, spirits at 40%, other tobacco products as other smoking tobacco, and
cigarettes at the default price. On that mix the model's duty per unit
cleared rises 5.7% for alcohol by 2026-27 and 19.0% for tobacco by 2027-28,
with the rate rises of February 2025 and February 2026 for alcohol and of
October 2024, November 2025 and October 2026 for tobacco, each of which
reaches its first full model year after 2024-25, and then holds. The OBR's
receipts per unit cleared keep rising, by 22.1% for alcohol and 48.2% for
tobacco by 2031-32. From 2027-28 the model's duty therefore falls short of
the OBR's forecast by more each year: on this construct, alcohol duty goes
from 7.6% above the OBR's 2024-25 receipts to 6.8% below its 2031-32
forecast, and tobacco duty from 1.9% above to 18.0% below. The construct's
product mix sets the 2024-25 gaps: charging all beer and cider at the beer
rate with no draught relief puts that line 22.4% above its receipts. A
dataset replaces the mix with its own. The later fall comes from the rates.

### Sources

The series and the figures above come from these files. The parser fixtures
in `policyengine_uk/tests/fixtures/obr_receipts/` keep the receipts sheets
of the two receipts workbooks unchanged.

| File | SHA-256 | Sheet and cells |
| --- | --- | --- |
| OBR October 2026 EFO, detailed forecast tables zip (`efo-october-2026-detailed-forecast-tables-zipfile.zip`) | `06ac908c69fce7d69dbfda4e16fc3b091a83bd8140ecd2f24990acd13d945fc2` | Holds the two workbooks below |
| October 2026 receipts tables, as published in the zip (`efo-october-2026-detailed-forecast-tables-receipts.xlsx`) | `d115705716d77b11c190385d41cb1924f30080c9331a8a386c04d4e65a368e95` | 4.11: rows 5 (cigarettes, unit in B5), 6 (non-cigarette, unit in B6), 8 (hand-rolled) and 9 (other tobacco products), columns C (2025-26 outturn) to I (2031-32); 4.12: rows 5 to 7 (beer and cider, wine, spirits), columns C to I, unit note B8, footnotes B9 and B10; 4.8: row 27 (tobacco duties, cash) and 4.12 rows 16 to 18 (alcohol receipts, accrued), for the comparison above |
| October 2026 policy tables (`efo-october-2026-detailed-forecast-tables-policy.xlsx`) | `cdcc2a06b100241bf3010bd159a4e5d43daef2348a3850797b1e88a308fd45fd` | 1.1: rows 95 (measure 19), 203 and 204 (measure 45), 446 and 447 (measure 95), 494 and 515 (totals for alcohol and tobacco duty) |
| October 2026 EFO (`economic-and-fiscal-outlook-october-2026-web-accessible.pdf`) | `9e0e9c340e35e603066f3124a614fcd68feadb3d5d10d1f76fb536e150e6225e` | Paragraphs 3.2, 4.43 and 4.44 |
| March 2026 receipts tables, as downloaded (`obr_efo_march_2026_receipts.xlsx`; the parser fixture of that name keeps only some of its sheets) | `f65b6cb7f96931d4abd85940794eb60f6f65afca8bbf16c74a4548bf92766a28` | 3.11: rows 5, 8 and 9, column C (2024-25 outturn); 3.12: rows 5 to 7, column C, and rows 16 to 18, column C (2024-25 receipts); 3.8: row 27, column D |

## Population data follow-ups

These formulas do not impute quantities or vehicle characteristics from the
existing combined `alcohol_and_tobacco_consumption`, fuel expenditure or vehicle
counts. Missing new inputs therefore contribute zero duty. Program metadata
marks alcohol, tobacco and vehicle excise duty as partial coverage. National
revenue estimates and distributional results require a separate data change:

1. Split alcohol and tobacco expenditure into products, including alcohol
   purchased in hospitality venues. Derive quantities using independently
   measured prices and strengths, retaining the original total expenditure.
2. Validate weighted totals against the
   [HMRC Alcohol Bulletin](https://www.gov.uk/government/statistics/alcohol-bulletin)
   and [Tobacco Bulletin](https://www.gov.uk/government/statistics/tobacco-bulletin).
   Record the fiscal year, population coverage, under-reporting adjustment,
   non-household purchases and cross-border differences before comparing totals.
3. Impute car characteristics jointly, preserving vehicle counts and ownership,
   using National Travel Survey or DVLA licensing data. Retain the registration,
   emissions, fuel and price correlations that determine the duty.
4. Identify road fuel gas consumption separately from petrol and diesel;
   do not allocate the same fuel spending to both.

Until these inputs are available, these additions support household calculations
and reforms on supplied quantities, not validated national revenue estimates.
