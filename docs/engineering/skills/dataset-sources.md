# Dataset Sources

Use this skill when changing simulation dataset loading, default datasets, H5
inputs, or interactions with upstream dataset materializers.

## Supported Source Shapes

`policyengine_uk.Simulation` and `Microsimulation` support several data inputs:

- explicit situations for single-household calculator-style simulations;
- pandas DataFrames;
- `policyengine_core.data.Dataset` instances;
- UK single-year and multi-year dataset schema objects;
- Hugging Face dataset URLs using `hf://...`;
- Google Cloud Storage dataset URLs using `gs://...`, with an optional
  `@generation-or-version` suffix;
- local H5 file paths.

Do not treat every string as a remote URL. Local file paths are valid dataset
sources when an upstream package has downloaded or materialized a remote dataset
to disk.

## Remote Datasets

UK directly supports `hf://` dataset URLs through the PolicyEngine Core
Hugging Face download path. It also supports `gs://` URLs by resolving the
requested object or version through Google Cloud Storage, downloading it into a
generation-keyed local cache, and then loading the resulting H5 file. Google
Cloud Storage sources require the `google-cloud-storage` package and application
default credentials.

Other remote schemes should be materialized before being passed into UK unless
UK adds explicit support for them. An upstream caller can resolve a remote
reference and pass the resulting local H5 path into `policyengine_uk`.

When debugging dataset failures, distinguish these stages:

1. a manifest or caller chooses the dataset reference;
2. the UK simulation dispatches `hf://` and `gs://` references to their
   respective download paths, while other callers may provide a local file;
3. UK loads the resulting H5 file and validates whether it is a single-year,
   multi-year, or core dataset file.

Errors at those stages require different fixes.

## ISA income input contracts

Calculator situations use additive savings inputs: `savings_interest_income`
is ordinary interest, while `tax_free_savings_income` is a separate cash-income
component. Its default is `individual_savings_account_interest_income`; an
explicit aggregate override, including zero, remains authoritative.

Existing unmarked datasets use the legacy contract: their savings-interest
column already includes the tax-free component. UK loads those records as
signed ordinary interest `N = G - T`, preserving explicit ISA and aggregate
inputs. There is no floor: `G < T` remains an override whose taxable result is
`max(0, N + other_investment_income)`, exactly as before. The adapter does not
infer an ISA amount from a tax-free aggregate.

`UKSingleYearDataset` accepts an optional `isa_income_contract` argument and
exposes a detached dictionary with exactly these fields:

```json
{"version": 1, "representation": "additive", "projection": "additive"}
```

The other valid pairs are `legacy_gross`/`legacy_gross` for raw legacy data
and `additive`/`legacy_gross` for normalized legacy data. Representation and
projection origin are separate: legacy projection grows the original gross
amount before subtracting the effective exemption. It must not grow the
already-normalized ordinary amount instead. New additive dataset projections
grow ISA interest alongside ordinary interest by the dataset's GDP-per-capita
rule; outside the stored horizon new inputs use their variable's own index.
Legacy-origin fallback retains the old gross-index calculation and unindexed
ISA carry-over, while explicit inputs and applicable ISA detail formulas take
priority. Legacy files containing only an aggregate exemption still have that
old exemption treatment; no ISA detail is invented during migration.

DataFrames carry this declaration in
`frame.attrs["policyengine_uk.isa_income_contract"]`. H5 files store UTF-8 JSON
under the same namespaced **root attribute**, never as an extra table or model
variable. Multi-year datasets and input-frame exports use per-year envelopes:

```json
{"version": 1, "years": {"2025": {"version": 1, "representation": "additive", "projection": "legacy_gross"}}}
```

A uniform single contract is also accepted when importing multiple years.
Every materialized year must be covered. Unknown versions, malformed metadata
and conflicting explicit object/file declarations fail with an `ISA income
contract` error. Omitted metadata means legacy data; the presence or relative
size of financial columns never chooses the representation.

UK copy, clone, household extraction, `from_simulation`, input-frame export and
single-/multi-year H5 round trips retain the projection origin and mark
normalized values as additive so they cannot be subtracted twice. Core Dataset
objects can carry the same `isa_income_contract` attribute; UK reads H5 root
metadata before Core's value loader discards it. External writers which
discard H5 attributes must explicitly preserve this declaration before their
output can be reloaded safely. Test routing and migration on synthetic frames
and small H5 fixtures, without downloading private datasets.

## Defaults

`policyengine_uk` does not silently choose a default dataset when no situation is
provided. Callers must pass `dataset=...` or opt into a default through the
configured environment variable.

Keep default dataset behavior explicit so calculator-style simulations,
microsimulations, and API workers do not accidentally diverge.

## Energy price declarations

Unlabelled dataset energy spending stays flat through the projection horizon.
Do not infer its price year from the dataset year, filename, URL or file format.
Legacy builds can hold FY2026-27 energy prices in a dataset labelled 2024.

An explicit declaration opts only `domestic_energy_consumption`,
`electricity_consumption` and `gas_consumption` into the existing generic annual
OBR consumer-price-index assumption as an interim price proxy. Other generic
uprating exclusions do not join this declaration or its reset group. For an
input whose producer receipt declares calendar-2024 prices, a caller can label
a local UK single-year H5 before constructing a simulation:

```python
from policyengine_uk import Microsimulation
from policyengine_uk.data import UKSingleYearDataset

dataset = UKSingleYearDataset(
    file_path="verified-input.h5",
    energy_price_basis={"period_type": "calendar_year", "period_value": 2024},
)
simulation = Microsimulation(dataset=dataset)
```

Use `fiscal_year` with the starting year when the receipt describes a UK
financial year. Both keys are required. The year must be an integer from 1
through 9999; malformed or conflicting caller/file declarations raise a clear
error. A caller's `None` leaves an existing file declaration intact.

The model retains the period kind as provenance but uses the January 1 index
level of the starting year for both calendar and fiscal price periods.
Projection multiplies the supplied amount by `I[target year] / I[price year]`.
This shared start-year convention approximates calendar/fiscal alignment;
generic CPI does not establish constant-consumption energy-price outturns or
an energy-specific forecast. Open [issue #2526](https://github.com/PolicyEngine/policyengine-uk/issues/2526)
tracks energy-specific index alignment and a sourced future assumption. The
original observation remains unchanged; a projected child's declaration records
its effective fiscal-year price basis so later extension does not apply the
original ratio twice.

When a declaration projects stored energy inputs, both January 1 dates must
fall on or after the selected index's earliest non-null value. An earlier
basis or target, including January 1 before a midyear start, raises a clear
error rather than using Core's backward first-value fallback. An index with
no usable history also raises an error for that projection. Unlabelled
observations and declarations with no relevant stored inputs retain their
existing behaviour without requiring index history.

Single-year H5 files store a JSON declaration in the root attribute
`energy_price_basis`. Multi-year files store it on each `/time_period/<year>`
group. Copy, save/load and filtering preserve the declaration. A Core Dataset
can declare the same named field or H5 attribute before UK conversion. HF/GCS
materializers retain the existing local-file routing. External multi-year
amounts and DataFrame inputs remain authoritative when loaded.

Disabling economic assumptions resets energy amounts and their declaration as
one group. A base year that supplies every stored later energy column replaces
those amounts and their declaration. With no overlapping base energy, later
amounts and metadata stay intact. A partial overlap resets shared columns only
when both declarations match exactly; otherwise the entire later energy group
and its declaration remain authoritative. Missing columns are never created.

Existing metadata-free private Microcosm releases stay flat under this
compatibility rule. They require an explicit caller migration based on a
verified receipt, or a producer release that exports the canonical declaration
matching that receipt. The producer must carry both period kind and year into
the H5 artifact; this consumer change does not retrofit that metadata or verify
the released private file.

## Bereavement-benefit split

Bereavement Support Payment rates remain unchanged under the
[2026 up-rating order, article 19](https://www.legislation.gov.uk/uksi/2026/148/article/19/made).
Older datasets combine it with CPI-uprated Widowed Parent's Allowance and
War Widow's Pension in `bsp_reported`. They keep CPI projection until the
producer separates those benefits.

Explicitly supplied `widowed_parents_allowance_reported` and
`war_widows_pension_reported` person columns together declare the completed
split used by the merged
[Microcosm PR #1383](https://github.com/PolicyEngine/microcosm/pull/1383),
including when every value in either column is zero. The automatic projector
then holds `bsp_reported` nominally flat; the separate allowance and
war-widow inputs still grow by CPI. Either column alone leaves BSP on the
legacy CPI path. Unclassified off-rate amounts that the producer retains in
`bsp_reported` receive the same nominal treatment. These can include Widowed
Parent's Allowance with an inherited additional pension above its rate;
freezing that CPI-linked component understates it.

Beyond the materialized projection horizon, the model holds BSP flat only
when its latest earlier input has both explicitly stored split inputs for
the same period. A calculated or carried default does not count, nor do
inputs supplied in different periods.
This also preserves the distinction when an external multi-year dataset
changes schema between observations. Supplied annual BSP amounts remain
authoritative. Disabling economic assumptions preserves those amounts when
either observation declares the split, rather than replacing separate BSP
with an older combined report.

UK single-year files, materialized Core datasets and their projected children
preserve both columns. Household situations retain their existing CPI behavior,
even when they supply the separate benefits. The change follows dataset
semantics, without inferring a split from a filename, model version or the
amount received. See [issue #2381](https://github.com/PolicyEngine/policyengine-uk/issues/2381).

## Tests

For dataset source routing, prefer stubbed tests that prove dispatch behavior
without downloading or opening private survey files.

Use real H5 files only when the test specifically needs schema or data behavior.
If the artifact is private, large, or credential-dependent, skip cleanly or keep
the verification outside the ordinary PR test suite.

## Data provenance and benefit take-up

`policyengine_uk.utils.data_source.built_from_data` distinguishes dataset-built
simulations from hand-entered situations, including supported clones, branches
and UK `build_from_situation` rebuilds. Council Tax Reduction and Housing Benefit
use this distinction for their take-up defaults: data-built simulations use
positive reported claims only (d1390 and d1455); situations also use their
per-benefit-unit `claims_all_entitled_benefits` flag. That flag is itself false
for every family on data-built simulations, as it was on main for any dataset
with a reporting family, so Child Tax Credit, Working Tax Credit and Income
Support take-up also follow reported claims there. Explicit inputs override
these defaults, including a future calibrated dataset column (uk-data#448).

Do not rebuild an existing data-built simulation by calling core's
`SimulationBuilder.build_from_dict` directly. In core 3.33.2 this leaves stale
dataset provenance, which copies inherit. Use UK `build_from_situation` instead.
