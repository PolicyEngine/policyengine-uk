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

## Tests

For dataset source routing, prefer stubbed tests that prove dispatch behavior
without downloading or opening private survey files.

Use real H5 files only when the test specifically needs schema or data behavior.
If the artifact is private, large, or credential-dependent, skip cleanly or keep
the verification outside the ordinary PR test suite.
