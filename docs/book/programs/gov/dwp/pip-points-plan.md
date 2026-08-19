# PIP point system (planned)

```{warning}
**Not yet modelled.** PolicyEngine UK currently takes the PIP daily-living
and mobility **band** as a categorical input (`pip_dl_category` and
`pip_m_category`, each `STANDARD | ENHANCED | NONE`) and multiplies by
the published weekly rate. The **points-system** logic that determines
which band a claimant falls into — 0–12 daily-living activities and 12
mobility activities, scored from the legislation — is **not** modelled.
This page captures the proposed scope, tracked under
[#1069](https://github.com/PolicyEngine/policyengine-uk/issues/1069).
```

## What PIP scoring actually is

The Personal Independence Payment is awarded on a **points-based**
assessment defined in [SI 2013/377][si-377] (the Social Security
(Personal Independence Payment) Regulations 2013):

- **Part 2: Daily living activities** — ten activities (preparing food,
  taking nutrition, managing therapy, washing and bathing, managing
  toilet needs, dressing and undressing, communicating verbally,
  reading and understanding signs and symbols, engaging with other
  people face-to-face, making budgeting decisions). Each activity has
  a set of descriptors with point values from 0 to 12.
- **Part 3: Mobility activities** — two activities (planning and
  following a journey, moving around). Same descriptor-based scoring.

The award rule:

| Total points (per component) | Award |
|-----------------------------|-------|
| 0–7 | None |
| 8–11 | Standard rate |
| 12+ | Enhanced rate |

Daily living and mobility are scored independently — a claimant can be
on standard daily-living and enhanced mobility, or any other
combination.

## Why the current categorical model is reasonable for microsim

For population-aggregate simulation, the categorical bands are
sufficient because:

- the FRS doesn't capture activity-level point scores at all,
- DWP's published caseload reports band counts (standard / enhanced)
  rather than activity scores,
- the calibrated `pip_dl_category` / `pip_m_category` in
  `policyengine-uk-data` are derived directly from FRS reported PIP
  payments and DWP outturn caseload.

So for headline distributional and fiscal analysis the categorical
inputs are correct.

## Where the point system would matter

Three reform scenarios that the categorical model can't answer:

1. **Activity-level descriptor reform** — e.g. the 2024 Conservative
   Green Paper proposed restricting points awarded for descriptors like
   "needs prompting to prepare food". A categorical input can't capture
   this; the categorical band wouldn't shift unless an analyst manually
   re-bands a synthetic distribution.
2. **Threshold reform** — changing the band thresholds (e.g. raising
   the standard-rate floor from 8 to 10 points). Same limitation.
3. **Targeted analysis by descriptor** — distributional questions like
   "how does the enhanced cohort split between mobility activities" need
   the underlying activity scores.

## Proposed scope

### Phase 1 — points-to-category mapping

- Add the threshold parameters under `gov/dwp/pip/`:
  - `daily_living/standard_threshold.yaml` (8)
  - `daily_living/enhanced_threshold.yaml` (12)
  - `mobility/standard_threshold.yaml` (8)
  - `mobility/enhanced_threshold.yaml` (12)
- Add per-activity score inputs as `pip_dl_activity_1_score` ...
  `pip_dl_activity_10_score`, `pip_m_activity_1_score`,
  `pip_m_activity_2_score`. Type: integer (Person, YEAR), default 0.
- Add derived variables `pip_dl_total_score` and `pip_m_total_score`
  summing the activity scores.
- Add `pip_dl_category_from_points` and `pip_m_category_from_points`
  that look up the band from the total score against the threshold
  parameters.
- Keep `pip_dl_category` / `pip_m_category` as the **input** the rest of
  the model reads, with a new switch parameter
  `gov.dwp.pip.use_point_system` (default `false`) that, when `true`,
  overrides the categorical input with the points-derived band.

This is a strict superset of the current model: the categorical input
remains authoritative by default, and analysts opting into the points
machinery (for reform analysis) get the activity-level surface.

### Phase 2 — descriptor-level parameters

- Per-activity descriptor tables under `gov/dwp/pip/descriptors/`,
  encoding the point value of each descriptor in SI 2013/377. The
  representation can be flat (one YAML per activity with a list of
  `(descriptor_id, points)` entries).
- A `pip_dl_activity_1_descriptor` (etc.) enum input that selects which
  descriptor applies; the activity score is then a parameter lookup.
- Reform-side: descriptor point values are then parameters that can be
  perturbed for "what if descriptor X scored 4 instead of 6" analyses.

### Phase 3 — data-side imputation

- The FRS provides PIP payment amounts but not descriptor selections.
  `policyengine-uk-data` would need to impute descriptor selections per
  claimant that are consistent with the observed band. The plausible
  approach is to draw uniformly across descriptor combinations that
  sum to the observed band, weighted by DWP-published "activities most
  commonly scoring above zero" tables.
- This phase is the heaviest and is only required to make Phase 2
  reforms work on the calibrated microsim. For the household
  calculator, users can input activity scores directly.

## Open questions

- Should the score inputs default to `None` (sentinel) or 0? Sentinel
  is cleaner when the points machinery is opt-in via the
  `use_point_system` flag.
- DWP's PIP review process distinguishes "ongoing" vs "fixed-term"
  awards. Should the model expose the award duration, or treat all
  current awards as ongoing? (Current model assumes ongoing.)
- The 2024 Green Paper considered moving some of the highest-points
  activities to a separate disability benefit — should the design
  anticipate that?

## References

- [The Social Security (Personal Independence Payment) Regulations 2013 (SI 2013/377)][si-377] — Parts 2 and 3 define the point system.
- DWP, [Personal Independence Payment: Assessment guide][assess-guide].
- DWP, [PIP statistics](https://www.gov.uk/government/collections/personal-independence-payment-statistics) — caseload by component and band.
- DWP, [Modernising support for independent living: the health and disability green paper (April 2024)][green-paper] — proposals to restrict descriptors.
- Issue: [#1069](https://github.com/PolicyEngine/policyengine-uk/issues/1069).
- Existing model: `pip_dl_category`, `pip_m_category`, `pip_dl`, `pip_m`.

[si-377]: https://www.legislation.gov.uk/uksi/2013/377
[assess-guide]: https://www.gov.uk/government/publications/personal-independence-payment-assessment-guide-for-assessment-providers
[green-paper]: https://www.gov.uk/government/consultations/modernising-support-for-independent-living-the-health-and-disability-green-paper
