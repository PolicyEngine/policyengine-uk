# Dataset Sources

Use this skill when changing simulation dataset loading, default datasets, H5
inputs, or interactions with upstream dataset materializers.

## Supported Source Shapes

`policyengine_uk.Simulation` and `Microsimulation` support several data inputs:

- explicit situations for single-household calculator-style simulations;
- pandas DataFrames;
- `policyengine_core.data.Dataset` instances;
- UK single-year and multi-year dataset schema objects;
- HuggingFace dataset URLs using `hf://...`;
- local H5 file paths that have already been materialized by an upstream
  resolver.

Do not treat every string as a remote URL. Local file paths are valid dataset
sources when an upstream package has downloaded or materialized a remote dataset
to disk.

## Remote Datasets

UK directly supports `hf://` dataset URLs through the existing HuggingFace
download path.

Other remote schemes, including `gs://`, should be materialized before being
passed into UK unless UK has explicit scheme support. The `.py` bundle/runtime
can resolve a manifest entry, materialize a remote dataset source, and then pass
the resulting local H5 path into `policyengine_uk`.

When debugging dataset failures, distinguish these stages:

1. manifest or caller chooses the dataset reference;
2. upstream resolver materializes remote references such as GCS to a local path;
3. UK loads the local H5 path and validates whether it is a single-year,
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
