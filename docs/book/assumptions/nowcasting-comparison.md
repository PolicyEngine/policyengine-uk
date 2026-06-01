# PolicyEngine vs Resolution Foundation nowcasting

The Resolution Foundation (RF) publishes a UK microsimulation nowcast as
part of its [Living Standards Outlook][lso] and pre-budget previews. RF
documents its methodology in the LSO appendix; PolicyEngine's approach is
spread across this repo, `policyengine-uk-data`, and the parameters under
[`gov/economic_assumptions/`](./growthfactors.md). This page summarises
how the two approaches differ at a high level so users can interpret
discrepancies between the two nowcasts.

For a focused write-up of how PolicyEngine generates the economic growth
factors, see [`growthfactors.md`](./growthfactors.md).

## Common ground

Both PolicyEngine and RF start from the same survey backbone — the **Family
Resources Survey** (FRS) plus its companion datasets (HBAI) — and project
it forward using a mix of:

- macroeconomic year-on-year growth rates (CPI, average earnings, RPI,
  CPIH),
- benefit and tax parameter uprating,
- a calibration step that reweights households to match published
  aggregates (caseloads, fiscal totals).

In broad strokes both nowcasts produce gross-to-net household incomes and
participation-weighted programme spending consistent with OBR-published
totals over the next two-to-three fiscal years.

## Where the methodologies diverge

### Earnings growth

| Aspect | Resolution Foundation | PolicyEngine UK |
|-------|------------------------|-----------------|
| Wage floor | Models the National Living Wage / NMW explicitly each year, lifting anyone below their age-appropriate minimum to the floor. | Earnings are uprated by the OBR average-earnings index without an explicit floor; minimum wage uprating is held in `gov/hmrc/minimum_wage/` and only enters when a reform invokes it. |
| Spillovers | Includes a spillover effect for workers just above the wage floor (compression of the lower wage distribution). | No automatic spillover; earnings shift uniformly with the OBR index. |
| NLW extensions | Models the 2024-25 extension of the NLW to 21- and 22-year-olds, and provisionally the 2029-30 extension to 18-20-year-olds. | NLW age bands are encoded in parameters (`gov/hmrc/minimum_wage`) but extensions only flow into outputs if a household's wage actually falls below the modelled floor — there is no explicit re-anchoring of earnings. |
| Beyond 2025-26 | Assumes the wage floor grows in line with average earnings. | Same effective behaviour, but driven by uprating rather than a wage-floor rule. |

**Practical implication.** Low-paid workers' incomes can grow faster under
the RF nowcast than under PolicyEngine because the wage floor binds and
ripples up; PolicyEngine treats them like everyone else under the OBR
earnings index.

### Benefit uprating

| Aspect | Resolution Foundation | PolicyEngine UK |
|-------|------------------------|-----------------|
| Working-age benefits | Uses statutory uprating with explicit overrides for announced policy (e.g. CoL Payments, benefit freezes). | Same approach. Parameters under `gov/dwp/` and `gov/hmrc/child_benefit/` track legislated rates; ad hoc payments live under `gov/treasury/cost_of_living_support`. |
| State Pension | Models the triple lock explicitly, using its own internal earnings/CPI forecasts. | Models the triple lock via `gov/dwp/state_pension/triple_lock/*.yaml`; the uprating value tracks announced DWP rates with a fallback to the maximum of earnings, CPI and the 2.5% floor. |

### Take-up

| Aspect | Resolution Foundation | PolicyEngine UK |
|-------|------------------------|-----------------|
| Approach | Uses HMRC/DWP outturn take-up rates and aligns simulated caseloads to published totals via calibration. | Same: each means-tested benefit has a `*_takeup_rate` parameter populated stochastically into `would_claim_*` flags in `policyengine-uk-data`, and the reweighting step in `policyengine-uk-data` enforces caseload alignment. |

### Calibration / reweighting

| Aspect | Resolution Foundation | PolicyEngine UK |
|-------|------------------------|-----------------|
| Targets | Aligns to a mix of HMRC, DWP and ONS aggregates. | Aligns to the same family of targets, but is publicly documented in `policyengine-uk-data` (`targets/`) and includes finer-grained local-authority targets for council tax and rents (see `policyengine-uk-data/datasets/local_areas/`). |

### Horizon

- **RF**: typically 4-5 years ahead in detail; long-run sensitivities run
  separately.
- **PolicyEngine**: 5+ years ahead using the OBR EFO supplemented by
  long-run equilibrium assumptions in `yoy_growth.yaml` (see
  [`growthfactors.md`](./growthfactors.md) and the
  `gov/economic_assumptions/README.md` for the 2031+ construction).

## Interpreting discrepancies

When PolicyEngine and RF disagree on a published statistic (e.g. relative
poverty, fiscal cost of a reform), the main sources of difference tend to
be:

1. **Wage-floor handling** — concentrated in low-pay groups (young
   workers, hospitality, retail). RF nowcasts higher real earnings growth
   here.
2. **Take-up calibration vintage** — both models drift between official
   take-up statistics releases; align to the same vintage before comparing.
3. **Local-area targets** — PolicyEngine's calibration includes
   LA-level rent and council tax targets that the public RF nowcast does
   not, which can shift housing-cost and disposable-income distributions.
4. **Long-run horizon** — beyond 2030 the divergence widens because the
   two models use different long-run rules; treat post-2030 figures as
   illustrative rather than authoritative.

## References

- Resolution Foundation, [Living Standards Outlook 2025][lso] — appendix
  details the RF nowcast methodology.
- Resolution Foundation, [budget preview reports](https://www.resolutionfoundation.org/publications/topic/budget-2025/) — operational pre-budget application.
- PolicyEngine, [growthfactors.md](./growthfactors.md) — economic
  assumption growth rates.
- PolicyEngine, [`policyengine_uk/parameters/gov/economic_assumptions/README.md`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/parameters/gov/economic_assumptions/README.md) — three-horizon construction of growth series.
- `policyengine-uk-data` — calibration targets and reweighting code.

[lso]: https://www.resolutionfoundation.org/publications/living-standards-outlook-2025/
