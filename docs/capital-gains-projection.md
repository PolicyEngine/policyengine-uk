# Capital gains projection

`Simulation` and `Microsimulation` accept an optional
`capital_gains_projection`. It specifies aggregate nominal realised-gains
growth before the response to a newly simulated reform. It is shared by
the reform and its baseline, and survives tax-parameter resets. Without
this argument, the model retains its existing GDP-per-capita projection.

This implements the projection interface in
[#2272](https://github.com/PolicyEngine/policyengine-uk/issues/2272).
Selecting a validated default, reconciling liabilities with receipts and
certifying Microcosm integration remain outstanding.

## Supplying a projection

The custom growth rates in this example are illustrative and are not the
OBR EOT scenario.

```python
from policyengine_uk import Simulation
from policyengine_uk.data.capital_gains_projection import CapitalGainsProjection

# Illustrative assumptions, not estimates of UK gains growth.
projection = CapitalGainsProjection(
    name="illustrative_gains_path",
    base_year=2024,
    annual_growth={2025: -0.10, 2026: 0.15},
    source="https://example.org/methodology",
    vintage="illustrative scenario",
    assumptions="Common composition; aggregate nominal gains before tax and response.",
)
simulation = Simulation(
    situation={"age": {2024: 45}, "capital_gains": {2024: 100_000}},
    capital_gains_projection=projection,
)
gains = simulation.calculate("capital_gains_before_response", 2026)
provenance = simulation.capital_gains_projection_metadata
```

Rates are changes, not multipliers: `-0.10` is a 10% fall. The year labels
are the start of a UK fiscal year: `2025` means FY2025–26. Every year after
`base_year` through `end_year` must be specified; finite rates greater than
−100% ensure positive growth factors. The configuration is immutable and
has a content fingerprint.

The caller must establish the gains observation period and measurement
basis. A dataset filename or calibration year does not establish either.
Keep the observed gains, losses and component amounts as supplied. Match
the projection to their before/after-loss and before/after-annual-exempt-
amount definition and population coverage.

## Amounts, weights and components

The model generates two dedicated parameter paths:

- `gov.economic_assumptions.yoy_growth.capital_gains` for dataset projection;
- `gov.economic_assumptions.indices.capital_gains` for household input carry-forward.

These are read-only generated paths. Attempting to change either through a
parameter reform raises an error; supply a `CapitalGainsProjection` through
`capital_gains_projection` instead. Reforms to the underlying GDP or
population assumptions remain supported and refresh the generated paths.

Both describe **per-record amounts**. For aggregate growth `g` and the
model's population growth `p`, the amount factor is `(1 + g) / (1 + p)`.
Dataset weights already grow by `1 + p`, so population is counted once.
The cumulative index uses these factors without intermediate rounding.
With no explicit projection, both paths copy the existing GDP-per-capita
series exactly, including its index rounding.

The common factor scales total gains, BADR, residential-property and
carried-interest amounts together, preserving component shares and signs.
It does not change which records realise gains, impute missing support or
classify BADR as an asset type. It also does not create losses or implement
loss carry-forward rules. This fixed-composition approximation requires
validation before use in a published costing. Data whose future weights
change nonuniformly require a separate reconciliation; the aggregate
identity assumes the model's uniform population uprating.

Explicit inputs for the requested year and supplied multi-year datasets
remain authoritative. They are not rescaled. A single-year dataset uses
`PROJECTION_END_YEAR` in `policyengine_uk/data/economic_assumptions.py` as
its general default extension horizon. An explicitly finite CGT projection
caps that default at the earlier of the general horizon and its own end
year. This caps the whole automatically extended dataset, including its
non-CGT inputs. Increasing the general horizon does not extend a finite
scenario: the EOT scenario still ends in FY2030–31.

An explicit extension outside the scenario span raises an error when CGT
inputs need projection. A household calculation also raises if carrying
an earlier CGT input would cross the supported span. A household without
any gains input still defaults to zero. There is no GDP fallback or
terminal extrapolation for an explicitly selected projection.

Pass the projection separately from the tax reform. Both simulations
start with that projection; the existing CGT realisation response then
operates on those gains. A tax reform must not be fitted back to an OBR
baseline revenue target. Combining an explicit projection with
`no_economic_assumptions` raises: omit the projection to freeze economic
assumptions.

## Experimental OBR EOT sensitivity

```python
from policyengine_uk.data.capital_gains_projection import obr_eot_projection

projection = obr_eot_projection()
```

This opt-in sensitivity uses Table 1.2 of the OBR's
[EOT relief costing supplement, physical page 5](https://obr.uk/docs/dlm_uploads/Supplementary-forecast-information-capital-gains-tax-relief-on-qualifying-disposals-costing.pdf#page=5),
which relates to the **November 2025 forecast**, published on 2 April 2026.
The row is "CGT financial assets (excluding carried interest) growth rates".
It is not the March 2026 forecast or an OBR projection of all realised gains.

| Fiscal year | Aggregate proxy growth |
|---|---:|
| 2025–26 | −1.6% |
| 2026–27 | 23.4% |
| 2027–28 | 11.6% |
| 2028–29 | 10.7% |
| 2029–30 | 10.2% |
| 2030–31 | 10.1% |

The 23.4% for FY2026–27 is the published Table 1.2 determinant. The
supplement does not decompose that increase into underlying gains,
tax-policy, timing or composition effects, so this scenario makes no
attribution among them.

The source's 64.4% for FY2024–25 is not applied to the observed FY2024–25
anchor. Paragraph 1.5 uses the financial-asset determinant excluding
carried interest to project an EOT chargeable-gains base after annual
exemption adjustments; paragraph 1.11 describes a liability forecast
underpinning growth. The series is not established as a policy-free,
pre-exemption gains determinant. Extending it to every component is an
explicit common-composition sensitivity. No additional forestalling
unwind is imposed because that could count the same timing effect twice.

For orientation, these are cumulative **per-record input factors**, relative
to FY2024–25, calculated with the model's March 2026 economic assumptions.
They are not revenue estimates or validation against OBR receipts.

| Year | Existing GDP per capita | CPI sensitivity | Experimental EOT proxy |
|---|---:|---:|---:|
| 2024 | 1.000000 | 1.000000 | 1.000000 |
| 2025 | 1.043799 | 1.034000 | 0.976966 |
| 2026 | 1.074280 | 1.057780 | 1.201012 |
| 2027 | 1.108982 | 1.078934 | 1.335388 |
| 2028 | 1.143359 | 1.100512 | 1.472385 |
| 2029 | 1.177205 | 1.122519 | 1.615461 |
| 2030 | 1.214291 | 1.144970 | 1.770654 |

The proxy does not necessarily reduce projected gains; its different
vintage and measurement basis are material. Regenerate this table from the
three parameter indices when updating the assumptions, dividing each
year's index by its FY2024–25 value.

## Validation and downstream integration

The projection metadata records source, vintage, aggregate and per-record
rates, population assumptions, supported years, fingerprints and model/core
versions. Include it in analysis outputs and cache keys alongside dataset
identity and policy settings. PE-UK's in-memory remote-dataset cache
separates different projections; persisted downstream caches must do so too.

Before selecting a replacement default:

1. Compare GDP per capita, a CPI-per-record sensitivity and the candidate
   path using the same observed dataset. To express CPI-per-record growth
   in this aggregate API, use `(1 + CPI) * (1 + population_growth) - 1`.
2. Compare gains, taxpayer counts, liabilities, static and behavioural
   reform revenue and distributions. Keep compatible HMRC observations
   separate from OBR forecasts.
3. Bridge liabilities to cash receipts by component and year. Account for
   residential payment timing, individuals versus trusts, tax-rate and
   exemption changes, and the unmodelled carried-interest transition.
   Explain residuals rather than treating raw receipts growth as gains
   growth or an exact receipts fit as validation.
4. Update Microcosm's projection helper to select the same configuration
   and read the dedicated growth path and fingerprint. Update its growth
   expectations, projected-entrant checks and release validation. This
   PE-UK change alone does not recertify a dataset/model pair.
5. Integrate the comparison into
   [uk-cgt-reform #2](https://github.com/PolicyEngine/uk-cgt-reform/issues/2).

Separate residential/financial paths, an independently evidenced
forestalling decomposition and a validated default are future work. This
interface accepts an evidenced aggregate path when one becomes available;
it does not estimate those assumptions itself.
