# Household excise duties

The model calculates alcohol duty, tobacco duty, vehicle excise duty on cars,
and duty on LPG and natural road fuel gas from supplied household inputs.
`household_tax` and `gov_tax` include these amounts once, alongside petrol and
diesel duty. The incidence assumption is full pass-through to consumers.

## Coverage and periods

Alcohol, tobacco and car duty calculations cover 2024/25 to 2026/27. The alcohol
parameter history starts on 1 August 2023; the preceding alcohol regime and a
complete 2023/24 calculation are outside this implementation. Tobacco rates
start on 22 November 2023. The new alcohol, tobacco and car formulas return their
default zero before 2024; that is an unmodelled period, not a statutory exemption.
Gas duty covers 2022/23 onwards and includes the announced September 2026,
December 2026 and March 2027 increases. Rates after the last dated entry stay
constant; these new parameters do not forecast future inflation increases.

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

The linear gas rates use the existing `fiscal_year_blend: true` machinery.
Petrol and diesel retain their existing calendar-year averaged rate path.
Monthly `fuel_duty` allocates one twelfth of each annual volume and uses the
model's annual rate; it does not represent duty on a dated purchase.

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

Source: [HMRC fuel duty rates 2026 to 2027](https://www.gov.uk/government/publications/fuel-duty-rates-for-2026-to-2027/fuel-duty-rates-2026-to-2027).

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
