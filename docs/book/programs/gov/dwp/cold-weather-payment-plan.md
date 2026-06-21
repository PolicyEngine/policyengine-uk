# Cold Weather Payment (planned)

```{warning}
**Not yet modelled.** The Cold Weather Payment (CWP) is a DWP payment
of **£25 per 7-day period of recorded cold weather** to qualifying
households in England, Wales and (historically) Northern Ireland.
PolicyEngine UK doesn't currently model it. This page captures the
proposed scope, tracked under
[#435](https://github.com/PolicyEngine/policyengine-uk/issues/435).

In Scotland the equivalent benefit is the **Winter Heating Payment**
(£59.75 per qualifying household per winter, replacing CWP from
February 2023) — also not modelled.
```

## What CWP is

Defined in [The Social Fund Cold Weather Payments (General)
Regulations 1988][cwp-1988] (SI 1988/1724). A household qualifies if
**all** of the following hold:

- The address is in a postcode covered by a weather station that
  recorded **7 consecutive days** at or below 0°C (forecast or
  observed) in the qualifying period (1 November – 31 March).
- A member of the benunit receives one of the **qualifying benefits**:
  Pension Credit; Income Support, JSA-IB, or ESA-IR (in either case
  with a disability-related premium, a child under 5, or in a few
  other circumstances); Universal Credit (with limited capability for
  work, a disability addition, or a child under 5).

The payment is £25 per 7-day cold period; multiple cold periods
trigger multiple payments. Outturn averages ~£100m to ~£200m/year
nationally depending on winter severity.

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

- New parameter `gov.dwp.cold_weather_payment.amount` = £25 (since
  the scheme's inception).
- New parameter
  `gov.dwp.cold_weather_payment.expected_periods_per_year` =
  long-run national average from DWP CWP statistics.
- New variable `cold_weather_payment_eligible` (BenUnit, YEAR) that
  fires if any benunit member receives one of the qualifying benefits
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

Different rules and a different administration — modelled as a
separate variable:

- `winter_heating_payment_scotland_eligible`: any benunit member on
  Pension Credit + Scotland residence (the WHP qualifying-benefit
  list is broader than CWP).
- `winter_heating_payment_scotland` = `amount` × `eligible` where
  `amount` is the flat per-household winter payment (£59.75 in
  2023-24, uprated subsequently).

## Data needs

- DWP, [Cold Weather Payment statistics](https://www.gov.uk/government/collections/cold-weather-payments-statistics) — caseload and expenditure by region by winter, primary calibration source.
- DWP-published WHP statistics (Scotland) — Phase 3 calibration.
- Met Office, [UK climate historic stations](https://www.metoffice.gov.uk/research/climate/maps-and-data/historic-station-data) — Phase 2 regional expected-period parameterisation.

The FRS gives `region` cleanly, so the geographic gate is no extra
data work for Phase 1/2.

## Open questions

- The qualifying-benefit list for CWP is narrower than for WHD —
  specifically the disability/child-under-5 triggers within UC and the
  legacy benefits. Should the eligibility be modelled as a single
  composite condition variable, or as separate `_via_uc` /
  `_via_legacy` / `_via_pc` flags?
- CWP averages ~£100m/year — well below most modelled benefits, but
  the marginal household-level impact is meaningful for the low-income
  pensioners and disabled households it targets. Worth modelling
  Phase 1 even if Phase 2 doesn't follow.
- Welsh Government has occasionally topped up CWP from devolved funds.
  Should the model expose a `wales_top_up` parameter for reform
  analyses?

## References

- [The Social Fund Cold Weather Payments (General) Regulations 1988 (SI 1988/1724)][cwp-1988].
- gov.uk, [Cold Weather Payment](https://www.gov.uk/cold-weather-payment).
- DWP, [Cold Weather Payment statistics](https://www.gov.uk/government/collections/cold-weather-payments-statistics).
- Scottish equivalent: [Winter Heating Payment (Scotland) Regulations 2023 (SSI 2023/8)](https://www.legislation.gov.uk/ssi/2023/8/contents).
- Issue: [#435](https://github.com/PolicyEngine/policyengine-uk/issues/435).

[cwp-1988]: https://www.legislation.gov.uk/uksi/1988/1724
