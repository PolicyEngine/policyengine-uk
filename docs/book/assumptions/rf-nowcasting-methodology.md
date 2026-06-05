# Resolution Foundation nowcasting methodology

This page summarises the Resolution Foundation (RF) microsimulation
nowcasting methodology, drawing on the appendix to RF's [Living Standards
Outlook 2025][lso] and the methodological notes in [Black holes and
consolidations][bhac]. It is a paired reference for PolicyEngine UK's
own assumptions — see [`growthfactors.md`](./growthfactors.md) for the
PolicyEngine growth rates and [`nowcasting-comparison.md`](./nowcasting-comparison.md)
for the high-level differences.

## Data foundation

RF's nowcast starts from the same UK household microdata that
PolicyEngine uses — the **Family Resources Survey (FRS)** and its
**Households Below Average Income (HBAI)** companion — combined with a
range of administrative aggregates used to anchor outputs to published
totals.

## Earnings growth

RF projects earnings forward year-by-year, with explicit minimum-wage
handling rather than uniform indexation:

1. **Wage floor**. In every projected year RF lifts anyone whose hourly
   wage falls below their age-appropriate **National Minimum Wage /
   National Living Wage** up to that floor. Floors come from the
   announced NMW/NLW schedule and (beyond 2025-26) are assumed to grow in
   line with average earnings.
2. **Spillover effect**. For workers whose wage sits just above the
   floor, RF applies a partial uplift to capture wage compression at the
   bottom of the distribution. The magnitude is calibrated to historical
   evidence on NMW spillovers (RF cites the Low Pay Commission research).
3. **NLW age extensions**. RF models the **2024-25 extension** of the
   NLW to 21- and 22-year-olds and, **provisionally**, the **2029-30
   extension** to 18- to 20-year-olds. These show up as discontinuities
   in the modelled wage floor for the affected cohorts.
4. **Uniform uprating beyond the floor**. Earnings above the floor are
   uprated equally for employees and the self-employed using OBR/BoE
   wage projections (constrained to ONS outturn data once published).

## Housing costs

RF separates rent and mortgage interest:

- **Private rents** are uprated using the ONS **Price Index of Private
  Rents (PIPR)** rather than a generic CPI-housing measure.
- **Social rents** are uprated according to the published social-rent
  policy in force in each year (typically CPI + 1 percentage point, with
  exceptions and caps where the government has announced freezes or
  variations).
- **Mortgage interest** flows are projected using OBR base-rate paths
  and the FRS-recorded interest portion of mortgage payments.

## Benefits

RF takes the legislated/announced statutory uprating of working-age and
pension-age benefits as given, layering on:

- **Caseload anchoring** to current **Universal Credit statistics** for
  in-payment caseloads, so simulated UC numbers track DWP outturn rather
  than drift with FRS take-up.
- **Take-up modelling** based on historical receipt rates by household
  type, used to scale the eligible population down to expected caseload.
- **Discretionary CoL payments** modelled as announced (and reset to
  zero once the policy ends).

## Inflation indices

RF uses the OBR EFO inflation paths (CPI, CPIH, RPI) as headline
indices, supplemented by ONS-published outturns once available. Beyond
the EFO forecast horizon RF holds rates flat at their final forecast
value rather than constructing a separate long-run rule.

## Calibration

RF aligns outputs to a mix of HMRC, DWP and ONS aggregates — most
prominently income tax receipts, NI receipts, UC caseload and
expenditure, and Pension Credit caseload. The exact target list and
weights vary across reports.

## Horizon

The Living Standards Outlook publishes detailed nowcasts about **four
to five fiscal years ahead** of the current outturn year. Longer-run
sensitivity analyses are run separately and are not part of the headline
nowcast.

## Where this differs from PolicyEngine

For a side-by-side comparison see
[`nowcasting-comparison.md`](./nowcasting-comparison.md). The three
biggest divergences are:

1. **Wage-floor / NLW handling** — RF models the floor and spillovers
   explicitly; PolicyEngine uprates earnings by the OBR average-earnings
   index and only invokes the NLW when a reform query asks for it.
2. **Housing-cost projection** — RF uses PIPR for private rents and
   social-rent policy for social rents; PolicyEngine uprates rents using
   `policyengine-uk-data` local-authority targets and ONS rent indices.
3. **Calibration targets** — PolicyEngine carries finer-grained
   local-authority targets for council tax and rents that the public RF
   nowcast does not surface.

## References

- Resolution Foundation, [Living Standards Outlook 2025][lso] — methodology
  appendix.
- Resolution Foundation, [Black holes and consolidations][bhac] — fiscal
  context and short methodology summary.
- Low Pay Commission, [National Minimum Wage research reports](https://www.gov.uk/government/publications/national-minimum-wage-low-pay-commission-research-reports) — empirical basis for the spillover assumptions.
- ONS, [Price Index of Private Rents (PIPR)](https://www.ons.gov.uk/economy/inflationandpriceindices/bulletins/priceindexofprivaterentsuk/latest).

[lso]: https://www.resolutionfoundation.org/publications/living-standards-outlook-2025/
[bhac]: https://www.resolutionfoundation.org/publications/black-holes-and-consolidations/
