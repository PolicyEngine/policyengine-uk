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
annual payment (£62.00 at the latest uprating,
[mygov.scot](https://www.mygov.scot/winter-heating-payment)), which
replaced Cold Weather Payment there in 2023. It isn't modelled either.
The separate Pension Age Winter Heating Payment, which replaced Winter
Fuel Payment in Scotland, is modelled under
`gov.social_security_scotland.pawhp`. Updated October 2026: amounts,
legislation and the Scotland and Northern Ireland position checked.
```

## What CWP is

Defined in [The Social Fund Cold Weather Payments (General)
Regulations 1988][cwp-1988] (SI 1988/1724). A household qualifies if
**all** of the following hold:

- The address is in a postcode linked to a weather station where the
  average temperature is recorded as, or forecast to be, **0°C or below
  over 7 consecutive days** between 1 November and 31 March.
- A member of the benefit unit receives a **qualifying benefit**:
  Pension Credit; Income Support, income-based JSA or income-related
  ESA with a disability or pensioner premium or a child under 5 (or,
  for ESA, in the support or work-related activity group); Universal
  Credit when not employed with a limited capability for work element,
  a disabled child element or a child under 5, or when employed with a
  disabled child element; or Support for Mortgage Interest with one of
  those premiums or a child under 5. The GOV.UK eligibility page has
  the exact conditions.

The payment is £25 per 7-day cold period, and each further cold
period triggers another payment. Spending varies a lot with the winter: in
2024-25, for example, about 1.4 million payments worth around £35
million were made in England and Wales
([DWP, April 2025](https://www.gov.uk/government/news/over-35-million-in-cold-weather-payments-support-paid-this-winter)).
DWP doesn't count actual payments through the winter; it publishes the
estimated number of eligible people at the start of each season and the
weekly triggers, from which payments can be estimated.

## Why this is harder than other DWP benefits

The eligibility test combines an administrative benefit check (clean
for PolicyEngine) with a **geographic weather event** (no FRS
analogue). Modelling the weather side has three plausible approaches:

1. **Expected-value parameterisation**: a single national
   `cold_weather_payments_expected_periods` parameter capturing the
   long-run-average number of 7-day cold periods triggered per winter.
   Multiply by `£25 × qualifying_household` to produce the expected
   annual payment. Easy to implement, accurate in aggregate, wrong in
   any specific winter.
2. **Regional weather mixing**: a per-region weather-event
   distribution (e.g. North East has more cold periods than London on
   average), parameterised from Met Office historic data. Captures the
   distributional skew without forecasting any particular winter.
3. **Year-specific lookups**: tabulate the DWP-published *Cold Weather
   Payment statistics* by region by year and use those as historical
   inputs. Most accurate for back-cast simulations; needs ongoing
   updating.

Recommendation: **option 2 (regional mixing)** for prospective analysis
and option 3 for back-casts where the data is available.

## Proposed scope

### Phase 1 — qualifying-benefit gate + expected-value payment

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

### Phase 2 — regional weather mixing

Add a `gov.dwp.cold_weather_payment.expected_periods_by_region` table
parameterised from Met Office observation data, and a household-side
lookup by `region`.

### Phase 3 — Scotland Winter Heating Payment

Paid by Social Security Scotland under
[The Winter Heating Assistance (Low Income) (Scotland) Regulations 2023](https://www.legislation.gov.uk/ssi/2023/16/contents)
(SSI 2023/16). The qualifying benefits are essentially the same as for
Cold Weather Payment (Pension Credit with no further condition; the
other benefits with the same disability, pensioner-premium or
child-under-5 conditions), assessed in a qualifying week (2 to 8
November in 2026), but the payment is a flat annual amount with no
weather trigger. So:

- `winter_heating_payment_eligible`: the Phase 1 eligibility rule plus
  residence in Scotland. Reuse the Phase 1 variable rather than a second
  copy of the benefit conditions.
- `winter_heating_payment` = `amount` × eligible, with `amount`
  uprated each year (£62.00 at the latest uprating).

## Data needs

- DWP, [Cold Weather Payment statistics](https://www.gov.uk/government/collections/social-fund-cold-weather-payments) — estimated eligible numbers at the start of each season and weekly triggers by weather station; the main calibration source.
- DWP-published WHP statistics (Scotland) — Phase 3 calibration.
- Met Office, [UK climate historic stations](https://www.metoffice.gov.uk/research/climate/maps-and-data/historic-station-data) — Phase 2 regional expected-period parameterisation.

The FRS gives `region` cleanly, so the geographic gate is no extra
data work for Phase 1/2.

## Open questions

- The qualifying-benefit list is narrower than for the Warm Home
  Discount in England and Wales, which now covers everyone on
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
