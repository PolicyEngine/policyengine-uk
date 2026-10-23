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
