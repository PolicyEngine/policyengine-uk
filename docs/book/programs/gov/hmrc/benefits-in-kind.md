# Benefits in Kind (planned)

```{warning}
**Not yet modelled.** This page captures the planned scope and roadmap for
adding benefits-in-kind (BiK) modelling to PolicyEngine UK. Tracked under
[#1654](https://github.com/PolicyEngine/policyengine-uk/issues/1654);
remove the warning and the "Planned" sections below once the MVP lands.
```

## Current state in the model

There is no BiK modelling in the repo today. The *integration hook*
already exists:

- `policyengine_uk/variables/gov/hmrc/income_tax/bases/taxable_employment_income.py`
  adds an `employment_benefits` term to taxable earnings.
- `policyengine_uk/variables/household/benefits/employment_benefits.py`
  currently only sums `statutory_sick_pay` and `statutory_maternity_pay` —
  i.e. statutory cash payments, not P11D-style benefits-in-kind.

So the slot exists, but nothing fills it.

## Planned scope

UK BiK has a long tail. Roughly 80% of the aggregate taxable BiK base is
captured by five categories — we will MVP these and defer the rest.

### Phase 1 — MVP

| Category | P11D section | Notes |
|----------|--------------|-------|
| Company cars | F | Biggest single category by value |
| Car fuel benefit | F | |
| Private medical and dental insurance | I | |
| Living accommodation | D | |
| Beneficial loans | H | Interest below the HMRC official rate |

### Phase 2 — moderate prevalence

Vans and van fuel (G); vouchers and credit cards (C); mileage allowances
above HMRC approved rates (E); relocation expenses above £8k (J); assets
transferred or placed at disposal (A, L).

### Phase 3 — long tail / niche

Services supplied (K); payments on employee's behalf (B); entertainment;
non-qualifying travel and subsistence; employer-paid income tax;
educational assistance.

### Exempt — out of scope

Trivial benefits under £50; one mobile phone; workplace parking and
nurseries; employer pension contributions; cycle-to-work; eye tests for
VDU users; pensions advice up to £500.

## Implementation plan

### Variables

- A new `benefit_in_kind` variable on `Person`, summing typed
  sub-components.
- One sub-variable per BiK category in
  `variables/gov/hmrc/income_tax/bik/` (`company_car_benefit`,
  `car_fuel_benefit`, `private_medical_benefit`,
  `living_accommodation_benefit`, `beneficial_loan_benefit`).
- Add `benefit_in_kind` to `employment_benefits` so it flows into
  `taxable_employment_income` through the existing hook.

### Parameters

New tree under `parameters/gov/hmrc/income_tax/bik/`:

- `company_car/appropriate_percentage_by_co2.yaml` (year-by-year CO2 bands)
- `company_car/fuel_charge_multiplier.yaml`
- `company_car/electric_vehicle_rates.yaml`
- `car_fuel/multiplier.yaml`
- `living_accommodation/cost_threshold.yaml` (currently £75k)
- `beneficial_loan/official_rate.yaml`
- `beneficial_loan/de_minimis.yaml` (currently £10k)
- `vouchers/...` (Phase 2)

### Knock-on effects

BiK feeds into adjusted net income, which means it touches:

- the personal allowance taper at £100k,
- the High Income Child Benefit Charge,
- the tapered annual allowance for pensions,
- **Class 1A NICs (employer side)** — not currently modelled in the repo;
  treated as a separate workstream.

### Tests

- Unit tests per BiK category against worked HMRC examples.
- Integration tests asserting BiK flows through to taxable employment
  income, ANI, and HICBC where applicable.

## Data needs and FRS coverage

| Component | FRS has flag? | FRS has value? | Calibration source |
|-----------|---------------|----------------|--------------------|
| Company car | Yes | No (no list price / CO2 / fuel) | HMRC *Benefits in Kind statistics*, *Company Car Tax statistics* |
| Car fuel | Partially (fuel-provided flag) | No | HMRC BiK statistics |
| Private medical insurance | Yes (employer-paid flag) | No | HMRC BiK statistics |
| Living accommodation | Yes (job-tied accommodation flag) | No | HMRC BiK statistics; SPI (restricted) |
| Beneficial loans | No reliable flag | No | HMRC BiK statistics; SPI (restricted) |

### Public sources

- **HMRC Benefits in Kind statistics** — annual P11D-based release;
  recipient counts and total taxable values by category and income band.
  Primary calibration target.
- **HMRC Company Car Tax statistics** — CO2 and fuel-type distributions.
- **HMRC Personal Incomes Statistics (SPI tables)** — published totals.
- **DVLA / SMMT** — new-car registrations for company-car list-price/CO2
  distributions.

### Restricted-access (HMRC Datalab)

- **SPI microdata** — actual P11D values per individual; gold standard
  but requires accreditation and stays in the secure environment.
- **RTI / PAYE** — payrolled BiK (growing share since 2016 mandatory
  payrolling reforms).

### Imputation approach (proposed)

1. Use FRS flags to decide *who* receives each BiK type.
2. For each type, draw a value from a distribution calibrated so the
   population total and income-band breakdown match HMRC's published BiK
   statistics — mirrors the second-stage imputation pattern flagged in
   [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621).
3. For company cars: either (a) skip the list-price/CO2 mechanics and
   assign a calibrated taxable value directly, or (b) layer a simplified
   CO2-band model over an imputed list-price distribution. Recommend (a)
   for MVP and (b) as a Phase-1.5 refinement.

## Effort estimate

- Framework wiring + a flat-value `benefit_in_kind` variable feeding the
  existing hook: ~1–2 days.
- Phase 1 MVP (five categories, calibrated imputation, knock-on effects
  through ANI/HICBC, tests): ~2 weeks.
- Trustworthy distributional version (CO2 bands modelled, beneficial-loan
  amounts, sensitivity-checked imputation): closer to a month, with most
  time on the data side rather than the rules.
- Class 1A NICs (employer side): separate workstream.

## Open questions

- Do we model Class 1A NICs (employer side) in the same effort, or split
  it out?
- Should BiK enter Universal Credit and legacy means tests as earned
  income? HMRC treats most BiK as taxable but UC reads earned income from
  RTI: payrolled BiK flows through, non-payrolled BiK does not — needs a
  decision.
- Pursue HMRC Datalab access for SPI/RTI microdata, or stick to
  public-aggregate calibration for now?
