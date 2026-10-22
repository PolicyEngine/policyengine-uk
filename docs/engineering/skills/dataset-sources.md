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

An explicit declaration opts the three stored energy amounts into their
existing annual OBR consumer-price-index assumption. For an input whose
producer receipt declares calendar-2024 prices, a caller can label a local
UK single-year H5 before constructing a simulation:

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

The model retains the period kind as provenance but uses its existing annual
index-year convention: CY2024 and FY2024-25 both use `I[2024]`. Projection
multiplies the supplied amount by `I[target year] / I[price year]`. This is
the existing generic CPI assumption, with no new energy-specific forecast or
precise fiscal/calendar price adjustment. A 2026 basis therefore stays unchanged
at target 2026 and can grow at target 2027. The original observation remains
unchanged; a projected child's declaration records its effective fiscal-year
price basis so later extension does not apply the original ratio twice.

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

## Tests

For dataset source routing, prefer stubbed tests that prove dispatch behavior
without downloading or opening private survey files.

Use real H5 files only when the test specifically needs schema or data behavior.
If the artifact is private, large, or credential-dependent, skip cleanly or keep
the verification outside the ordinary PR test suite.
