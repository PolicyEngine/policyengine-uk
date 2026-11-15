# PIP point system (partly modelled)

```{warning}
**Partly modelled.** PolicyEngine UK sets the PIP daily-living and
mobility **band** in `pip_dl_category` and `pip_m_category` (each
`STANDARD | ENHANCED | NONE`) and multiplies by the published weekly rate.
A band can be given as an input or derived from total points
(`pip_dl_points`, `pip_m_points`) against the 8- and 12-point thresholds.
The activity-level logic (ten daily-living activities and two mobility
activities, with descriptors worth 0 to 12 points under the legislation)
is **not** modelled.
This page captures the proposed scope, tracked under
[#1069](https://github.com/PolicyEngine/policyengine-uk/issues/1069).
```

```{admonition} Status, October 2026
A first step merged on 21 October 2026 as
[#1661](https://github.com/PolicyEngine/policyengine-uk/pull/1661): total
points inputs (`pip_dl_points`, `pip_m_points`) and the 8- and 12-point
thresholds under `gov.dwp.pip.{daily_living,mobility}.points_thresholds`.
The category is derived from points only when no category is given as an
input for the year. A category given for a year is stored for everyone in
the simulation, with NONE for anyone not given one. Otherwise the person's
latest assessed points (not -1) for that year or an earlier one set the
category, except that
a category given for an earlier year carries forward unless those points are
for a later year than it; with neither, the category is NONE
(`policyengine_uk/utils/pip.py`). That is a simpler form of Phase 1 below:
no per-activity scores and no `use_point_system` switch, since a category
input already takes precedence over the formula.

No data path supplies points yet. The datasets store categories, not
points, so points play no part in microsimulation. The companion PR,
[policyengine-uk-data #408](https://github.com/PolicyEngine/policyengine-uk-data/pull/408)
(points imputed from the observed categories), was closed in June 2026
in the uk-data archive clean-up, with PIP points derivation to move into
Microcosm UK's source stages
([microcosm #145](https://github.com/PolicyEngine/microcosm/issues/145))
once the input variables existed here. Microcosm #145 closed on 16 October
2026 with that item dropped, because the variables did not exist yet.
```

## What PIP scoring actually is

The Personal Independence Payment is awarded on a **points-based**
assessment defined in Schedule 1 to [SI 2013/377][si-377] (the Social
Security (Personal Independence Payment) Regulations 2013):

- **Part 2: Daily living activities**: ten activities (preparing food,
  taking nutrition, managing therapy, washing and bathing, managing
  toilet needs, dressing and undressing, communicating verbally,
  reading and understanding signs, symbols and words, engaging with other
  people face-to-face, making budgeting decisions). Each activity has
  a set of descriptors with point values from 0 up to 12; the top
  value varies by activity.
- **Part 3: Mobility activities**: two activities (planning and
  following a journey, moving around), each with descriptors worth up
  to 12 points.

The award rule:

| Total points (per component) | Award |
|-----------------------------|-------|
| 0–7 | None |
| 8–11 | Standard rate |
| 12+ | Enhanced rate |

Daily living and mobility are scored independently, so a claimant can be
on standard daily-living and enhanced mobility, or any other
combination.

## Why the current categorical model is reasonable for microsim

For population-aggregate simulation, the categorical bands are
sufficient because:

- the FRS doesn't capture activity-level point scores at all,
- DWP's regular PIP statistics report the caseload by award level
  (standard / enhanced) rather than activity scores; per-activity figures
  appear only in one-off publications such as the evidence-pack tables
  cited under Phase 3,
- the data (both Microcosm UK, the certified default since October 2026,
  and the Enhanced FRS from policyengine-uk-data, which it replaced) sets
  `pip_dl_category` and `pip_m_category` by comparing the weekly PIP daily-living and mobility
  amounts respondents report in the FRS with the standard and enhanced
  rates.

So for headline distributional and fiscal analysis the categorical
inputs are correct.

## Where the point system would matter

Three reform scenarios that the categorical model can't answer:

1. **Activity-level descriptor reform**: for example, the April 2024
   green paper consulted on changing the descriptors, and the March 2025 *Pathways to
   Work* green paper proposed requiring at least four points in one
   daily-living activity for the daily-living component. The government
   withdrew the four-point change in July 2025, pending a review of the
   PIP assessment. A categorical input can't capture
   this; the categorical band wouldn't shift unless an analyst manually
   re-bands a synthetic distribution.
2. **Threshold reform**: changing the band thresholds (for example raising
   the standard-rate floor from 8 to 10 points). The thresholds are now
   parameters, so this works for households entered with points, but not in
   microsimulation, where the data supply bands rather than points.
3. **Targeted analysis by descriptor**: distributional questions like
   "how does the enhanced cohort split between mobility activities" need
   the underlying activity scores.

## Proposed scope

### Phase 1: points-to-category mapping

- Threshold parameters: done in #1661 as
  `gov.dwp.pip.{daily_living,mobility}.points_thresholds.{standard,enhanced}`
  (8 and 12).
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

### Phase 2: descriptor-level parameters

- Per-activity descriptor tables under `gov/dwp/pip/descriptors/`,
  encoding the point value of each descriptor in SI 2013/377. The
  representation can be flat (one YAML per activity with a list of
  `(descriptor_id, points)` entries).
- A `pip_dl_activity_1_descriptor` (etc.) enum input that selects which
  descriptor applies; the activity score is then a parameter lookup.
- Reform-side: descriptor point values are then parameters that can be
  perturbed for "what if descriptor X scored 4 instead of 6" analyses.

### Phase 3: data-side imputation

- The FRS provides PIP payment amounts but not descriptor selections.
  The data (Microcosm UK, as the replacement dataset) would need to
  impute descriptor selections per claimant that are consistent with the observed band. The plausible
  approach is to draw descriptor combinations whose total falls in the
  observed band, weighted by the point-score distributions for
  each daily-living activity that DWP published in the
  [Pathways to Work evidence pack](https://www.gov.uk/government/consultations/pathways-to-work-reforming-benefits-and-support-to-get-britain-working-green-paper/pathways-to-work-evidence-pack-chapter-2-reforming-the-structure)
  (chapter 2, Tables 2.27 and 2.28: working-age, normal-rules claimants
  awarded the daily living component in England, Wales and abroad, January
  2025 caseload; the pack has no per-activity mobility table).
- This phase is the heaviest and is only required to make Phase 2
  reforms work on the calibrated microsim. For the household
  calculator, users can input activity scores directly.

## Open questions

- Should the score inputs default to `None` (sentinel) or 0? Sentinel
  is cleaner when the points machinery is opt-in via the
  `use_point_system` flag. (#1661's total points inputs use -1 for "not
  assessed".)
- DWP's PIP review process distinguishes "ongoing" vs "fixed-term"
  awards. Should the model expose the award duration, or treat all
  current awards as ongoing? (Current model assumes ongoing.)
- The outcome of the PIP assessment review may change descriptors or
  the scoring rule; the descriptor-parameter design in Phase 2 should
  make such changes a parameter edit.

## References

- [The Social Security (Personal Independence Payment) Regulations 2013 (SI 2013/377)][si-377]: Schedule 1, Parts 2 and 3 define the point system.
- DWP, [Personal Independence Payment: Assessment guide][assess-guide].
- DWP, [PIP statistics](https://www.gov.uk/government/collections/personal-independence-payment-statistics): caseload by component and band.
- DWP, [Modernising support for independent living: the health and disability green paper (April 2024)][green-paper]: proposals on the descriptors.
- DWP, [Pathways to Work: Reforming Benefits and Support to Get Britain Working (March 2025)](https://www.gov.uk/government/consultations/pathways-to-work-reforming-benefits-and-support-to-get-britain-working-green-paper): the four-point proposal.
- Issue: [#1069](https://github.com/PolicyEngine/policyengine-uk/issues/1069).
- Existing model: `pip_dl_category`, `pip_m_category`, `pip_dl_points`, `pip_m_points`, `pip_dl`, `pip_m`, and the thresholds under `gov.dwp.pip.{daily_living,mobility}.points_thresholds`.

[si-377]: https://www.legislation.gov.uk/uksi/2013/377
[assess-guide]: https://www.gov.uk/government/publications/personal-independence-payment-assessment-guide-for-assessment-providers
[green-paper]: https://www.gov.uk/government/consultations/modernising-support-for-independent-living-the-health-and-disability-green-paper
