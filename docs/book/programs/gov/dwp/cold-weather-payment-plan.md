# Cold Weather Payment (planned)

```{warning}
**Not yet modelled.** The Cold Weather Payment (CWP) is a DWP payment
of **£25 per 7-day period of very cold weather** to qualifying
households in England and Wales. Northern Ireland runs its own scheme
on the same terms (1 November 2026 to 31 March 2027,
[nidirect](https://www.nidirect.gov.uk/articles/cold-weather-payment)).
PolicyEngine UK doesn't model it. This page sets out the proposed
scope, tracked in
[#435](https://github.com/PolicyEngine/policyengine-uk/issues/435).

In Scotland the equivalent is the **Winter Heating Payment**, a flat
annual payment (£62.00 from April 2026, regulation 9 of
[SSI 2023/16](https://www.legislation.gov.uk/ssi/2023/16/contents) as
amended), which
replaced Cold Weather Payment there from winter 2022-23 (first paid in
February 2023). It isn't modelled either.
The separate Pension Age Winter Heating Payment, which replaced Winter
Fuel Payment in Scotland, is modelled under
`gov.social_security_scotland.pawhp`. Updated October 2026: amounts,
legislation and the Scotland and Northern Ireland position checked.
```

## What CWP is

Defined in [The Social Fund Cold Weather Payments (General)
Regulations 1988][cwp-1988] (SI 1988/1724). A claimant qualifies if
**all** of the following hold:

- The address is in a postcode linked to a weather station where the
  average temperature is recorded as, or forecast to be, **0°C or below
  over 7 consecutive days** between 1 November and 31 March.
- A member of the benefit unit receives a **qualifying benefit**:
  Pension Credit; income-related ESA in the support or work-related
  activity group, or with a severe or enhanced disability premium, a
  pensioner premium, a disabled child or a child under 5 (Income Support
  and income-based JSA qualify on a similar test, under which the
  disability, higher pensioner and disabled child premiums also count);
  Universal Credit when neither the claimant nor a partner is employed
  or gainfully self-employed and someone has limited capability for
  work or there is a child under 5, or, whether working or not, when the
  award includes a disabled child amount; or Support for Mortgage
  Interest, either while treated as entitled to Pension Credit (no
  further condition) or with one of those premiums or children. The
  [GOV.UK eligibility page](https://www.gov.uk/cold-weather-payment/eligibility)
  summarises them; regulation 1A has the full conditions.
- The home is in England or Wales, and the claimant doesn't live in a
  care home, an independent hospital or certain other accommodation,
  unless the family includes a child under 5 or child tax credit
  includes a disability element (regulation 1A(4) and (8)).

The payment is £25 per 7-day cold period, and each further cold
period triggers another payment. Spending varies a lot with the winter: in
2024-25, for example, about 1.4 million payments worth around £35
million were made in England and Wales
([DWP, April 2025](https://www.gov.uk/government/news/over-35-million-in-cold-weather-payments-support-paid-this-winter)).
DWP doesn't count actual payments through the winter; it publishes the
estimated number of eligible people at the start of each season and the
weekly triggers, from which payments can be estimated.

## Why this is harder than other DWP benefits

The eligibility test combines an administrative benefit check (mostly
covered by existing PolicyEngine variables, though Support for Mortgage
Interest and the legacy pensioner premium aren't modelled) with a
**geographic weather event** (no FRS analogue). Modelling the weather side has three plausible approaches:

1. **Expected-value parameterisation**: a single national
   `gov.dwp.cold_weather_payment.expected_periods_per_year` parameter
   capturing the long-run-average number of 7-day cold periods triggered
   per winter. Multiply by £25 and by the qualifying benefit-unit flag to
   produce the expected annual payment. Easy to implement, accurate in aggregate, wrong in
   any specific winter.
2. **Regional weather mixing**: a per-region weather-event
   distribution (for example, the North East has more cold periods than
   London on average), parameterised from DWP's trigger counts by
   weather station. Captures the
   distributional skew without forecasting any particular winter.
3. **Year-specific lookups**: tabulate the DWP-published *Cold Weather
   Payment estimates* by weather station by year (mapped to regions
   through DWP's postcode-district lists) and use those as historical
   inputs. Most accurate for back-cast simulations; needs ongoing
   updating.

Recommendation: **option 2 (regional mixing)** for prospective analysis
and option 3 for back-casts where the data is available.

## Proposed scope

### Phase 1: qualifying-benefit gate and expected-value payment

- New parameter `gov.dwp.cold_weather_payment.amount` = £25. The amount
  was lower in earlier years, so take any backdated values from the
  amendment history of SI 1988/1724.
- New parameter
  `gov.dwp.cold_weather_payment.expected_periods_per_year` =
  long-run national average from DWP CWP statistics.
- New variable `cold_weather_payment_eligible` (BenUnit, YEAR) that
  fires if any benefit unit member receives one of the qualifying benefits
  with the relevant addition / age trigger.
- New variable `cold_weather_payment` (BenUnit, YEAR) = `amount` ×
  `expected_periods_per_year` × `eligible`.

This delivers a model that gets the policy-relevant slice right
(*who* qualifies for CWP and how it interacts with their other
benefits) at the cost of smoothing year-to-year weather variance.

### Phase 2: regional weather mixing

Add a `gov.dwp.cold_weather_payment.expected_periods_by_region` table
parameterised from DWP's trigger counts by weather station, and a
household-side lookup by `region`.

### Phase 3: Scotland's Winter Heating Payment

Paid by Social Security Scotland under
[The Winter Heating Assistance (Low Income) (Scotland) Regulations 2023](https://www.legislation.gov.uk/ssi/2023/16/contents)
(SSI 2023/16). The qualifying benefits are essentially the same as for
Cold Weather Payment (Pension Credit with no further condition; the
other benefits with the same disability, pensioner-premium or
child-under-5 conditions), assessed in a qualifying week (2 to 8
November in 2026), but the payment is a flat annual amount with no
weather trigger. So:

- `winter_heating_payment_eligible`: the Phase 1 benefit conditions,
  without Cold Weather Payment's care-home and England-and-Wales
  conditions (and without the child tax credit disability element,
  which Winter Heating Payment dropped in 2025), plus residence in
  Scotland in the qualifying week. Reuse the Phase 1 benefit-condition
  variable rather than a second copy of the benefit conditions.
- `winter_heating_payment` = `amount` × eligible, with `amount`
  uprated each year (£62.00 from April 2026).

## Data needs

- DWP, [Cold Weather Payment statistics](https://www.gov.uk/government/collections/social-fund-cold-weather-payments): estimated eligible numbers at the start of each season and weekly triggers by weather station. The main calibration source.
- Social Security Scotland's Winter Heating Payment statistics: Phase 3 calibration.
- DWP's trigger counts by weather station (Table 3 of each season's
  *Cold Weather Payment estimates*), mapped to regions through DWP's
  postcode-district lists: Phase 2 regional expected-period
  parameterisation. The Met Office's
  [historic station data](https://www.metoffice.gov.uk/research/climate/maps-and-data/historic-station-data)
  gives only monthly series for 37 stations, so it can serve as a
  cross-check but can't count 7-day cold periods.

The FRS records `region`, from which the model derives `country`, so the
England-and-Wales and Scotland gates need no extra data. Region is a
coarse stand-in for the weather-station areas that trigger payments, so
Phase 2 models a regional average, not individual stations.

## Open questions

- The qualifying-benefit list is narrower than for the Warm Home
  Discount in England and Wales, which now covers bill-payers on
  Universal Credit, Housing Benefit, income-related ESA or Pension
  Credit. Model the eligibility as one composite variable, shared with
  the Scottish Winter Heating Payment, or as separate flags by route
  (Universal Credit, legacy benefits, Pension Credit)?
- Spending is small next to most modelled benefits, but the payment
  matters to the low-income pensioners and disabled households it
  targets. Phase 1 is worth doing even if Phase 2 doesn't follow.

## References

- [The Social Fund Cold Weather Payments (General) Regulations 1988 (SI 1988/1724)][cwp-1988].
- gov.uk, [Cold Weather Payment](https://www.gov.uk/cold-weather-payment).
- DWP, [Cold Weather Payment statistics](https://www.gov.uk/government/collections/social-fund-cold-weather-payments).
- Scottish equivalent: [The Winter Heating Assistance (Low Income) (Scotland) Regulations 2023 (SSI 2023/16)](https://www.legislation.gov.uk/ssi/2023/16/contents); [mygov.scot](https://www.mygov.scot/winter-heating-payment).
- Northern Ireland: [nidirect, Cold Weather Payment](https://www.nidirect.gov.uk/articles/cold-weather-payment).
- Issue: [#435](https://github.com/PolicyEngine/policyengine-uk/issues/435).

[cwp-1988]: https://www.legislation.gov.uk/uksi/1988/1724
