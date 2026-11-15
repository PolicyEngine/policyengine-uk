# Capital gains distribution

```{note}
**Planning page, updated October 2026.** Tracks
[#818](https://github.com/PolicyEngine/policyengine-uk/issues/818)
(model gains jointly across income groups) and
[#817](https://github.com/PolicyEngine/policyengine-uk/issues/817)
(don't impute gains to households with no wealth). The imputation lives
in the data build, not in this repo. Most of what this page set out to
fix in May 2026 has since been addressed in
[Microcosm UK](https://github.com/PolicyEngine/microcosm), by a different
method from the one it proposed. Microcosm UK 2024-25 replaced the
Enhanced FRS from
[policyengine-uk-data](https://github.com/PolicyEngine/policyengine-uk-data)
as the certified UK default dataset on 21 October 2026
([policyengine.py#685](https://github.com/PolicyEngine/policyengine.py/pull/685),
released in policyengine.py 6.10.0); the Enhanced FRS can still be loaded
by name. What remains is listed at the end of this page.
```

## How the model uses capital gains

`capital_gains_before_response` is a person-level input, uprated through
`gov.economic_assumptions.indices.capital_gains`, which follows OBR
per-capita GDP growth unless a simulation supplies a
`CapitalGainsProjection`
([#2274](https://github.com/PolicyEngine/policyengine-uk/pull/2274); see
the [capital gains projection guide](https://github.com/PolicyEngine/policyengine-uk/blob/main/docs/capital-gains-projection.md)).
`capital_gains_tax` charges `capital_gains` (these gains plus any
behavioural response) at the main CGT rates, with three components
charged at their own rates (all added by
[#1861](https://github.com/PolicyEngine/policyengine-uk/pull/1861)):

- `capital_gains_badr`: gains qualifying for Business Asset Disposal
  Relief or Investors' Relief, at the relief rate up to the lifetime
  limit;
- `capital_gains_residential_property`: gains on UK residential
  property, at the residential rates;
- `capital_gains_carried_interest`: carried interest, at the carried
  interest rates.

Each is a component of the total, not an addition to it.

Behavioural responses: `capital_gains_behavioural_response` changes
realisations using an elasticity with respect to the retention rate
(`relative_capital_gains_retention_rate_change`) or the marginal tax
rate. Gains use `gov.simulation.capital_gains_responses.elasticity`,
which is 1.0 by default (since
[#2419](https://github.com/PolicyEngine/policyengine-uk/pull/2419),
October 2026), so a reform that changes a person's marginal rate on gains
changes their realisations unless a user sets it to 0; the
[capital gains realisation response](capital-gains-responses.md) page
explains it.
When `gov.simulation.capital_gains_responses.separate_badr_elasticity`
is true (false by default), gains qualifying for BADR respond at
`badr_elasticity` instead (1.4, the value the OBR used for these gains
in its costing of the October 2024 rate rises, published in January
2025), through `capital_gains_badr_elasticity`.

## How the gains are imputed

### Enhanced FRS: one distribution per income band

The Enhanced FRS (policyengine-uk-data, the certified default until
21 October 2026) fits a spline to the Advani and Summers gains
percentiles within each income band and draws each household's gains
from its band. The spline alone cannot produce gains above about £2m, so
policyengine-uk-data also stacks 30 donor households for each HMRC
size-of-gain band from £500,000 up (from £12,300 up before release
1.59.0) and calibrates to HMRC counts and amounts of gains by band. #818
asks for gains to be modelled across all income groups together rather
than each group independently, to avoid overfitting. Fitting band by band
means that:

- each band is fitted on its own, so the joint distribution of income
  and gains has breaks at band boundaries;
- two people in the same band draw from the same distribution however
  different their incomes;
- gains depend on income only, not on wealth, so they can be imputed to
  households with no assets (#817).

### Microcosm UK

Microcosm builds gains in six stages (see the UK
[sources specification](https://github.com/PolicyEngine/microcosm/blob/main/packages/microcosm-build/src/microcosm/build/uk/spec/sources.yaml)):

1. **Support split** (`cgt_support_split`). Within each income band of
   HMRC Capital Gains Tax statistics Table 3, the households with the
   most investable wealth (gross financial wealth, corporate wealth such
   as shares and investment funds, and property other than the main
   home) are split into lighter copies, so
   that there are enough rows to hold the largest gains.
2. **Who might have gains** (`cgt_incidence_clone`). Every household is
   cloned at half its weight, and the clone's oldest adult draws a prior
   gain from the Advani and Summers (2020) gains percentiles for their
   income band (*Capital Gains and UK Inequality*, CAGE Working Paper
   465).
3. **How much** (`hmrc_cgt_gains_spine`). Amounts are redrawn so that
   gains match HMRC Table 3 for 2024-25, which counts taxpayers and
   gains **jointly by size of gain and taxable income**, conditioned on
   Tables 1, 2.1a, 5 and 6. Within each income band, age group and
   region group, the largest gains go to the gainers ranked highest on
   household investable wealth (weighted three quarters) and the prior
   gain (one quarter).
4. **Weight anchor** (`cgt_incidence_anchor`). After the redraw, clones
   with gains at or below the annual exempt amount, or with losses,
   carry far more weight than the Advani and Summers reporter
   composition implies for the number of liable gainers (HMRC publishes
   no count of them), so the excess weight is moved back to each clone's
   paired original.
5. **Residential property** (`cgt_residential_split`). Gains on UK
   residential property are fitted to Table 8 (2024-25 residential
   property disposals) by splitting households into weighted copies,
   which fills `capital_gains_residential_property`.
6. **What kind** (`hmrc_cgt_asset_type_spine`). Of the other liable
   gainers, those claiming BADR or Investors' Relief are fitted band by
   band to Table 4.1, which fills `capital_gains_badr`. Every one of them
   is also given a main asset type from Table 7 (gains by asset type,
   2023-24), for diagnostics only. Carried interest (HMRC Table 9) is not
   imputed.

All the HMRC tables come from the 2026 release of the Capital Gains Tax
statistics (published 27 August 2026), through Microcosm's pinned
Chronicle feed.

Against #818: gains are now fitted to the published joint distribution
of gain size and taxable income, not band by band. Against #817:
within each income band, the largest gains go mainly to the wealthiest
households, through the wealth-weighted ranking in stage 3. Microcosm's release checks also include a projection check
on people just below the annual exempt amount
(`uk_cgt_projection_entrants` in `gates.json`), so that
uprating does not push implausible numbers of them into paying CGT in
later years.

## What is left

- **A zero-wealth test.** Add a test, here or in Microcosm, that no
  positive gains sit on households with zero investable wealth. Neither
  repo asserts this directly yet, so #817 should stay open until it
  does.
- **Close #818** once the certified Microcosm UK dataset's diagnostics
  confirm the Table 3 fit (Microcosm UK has been the certified default
  since 21 October 2026); link them from the issue.
- **Elasticities by group.** Responses use one main elasticity and one
  BADR elasticity. With the joint distribution in place, an elasticity
  that varies by income or size of gain becomes possible, at the cost
  of more parameters to justify.
- **Wealth source.** Investable wealth comes from Microcosm's Wealth
  and Assets Survey imputation. Its quality limits how well #817 can be
  met.

The quantile regression forest approach proposed here in May is no
longer needed for this.

## References

- Issues: [#818](https://github.com/PolicyEngine/policyengine-uk/issues/818), [#817](https://github.com/PolicyEngine/policyengine-uk/issues/817).
- CGT components: [#1861](https://github.com/PolicyEngine/policyengine-uk/pull/1861).
- HMRC, [Capital Gains Tax statistics](https://www.gov.uk/government/statistics/capital-gains-tax-statistics).
- Advani, A. and Summers, A. (2020), *Capital Gains and UK Inequality*, CAGE Working Paper 465.
- Microcosm UK [sources specification](https://github.com/PolicyEngine/microcosm/blob/main/packages/microcosm-build/src/microcosm/build/uk/spec/sources.yaml) (stages `cgt_support_split`, `cgt_incidence_clone`, `hmrc_cgt_gains_spine`, `cgt_incidence_anchor`, `cgt_residential_split`, `hmrc_cgt_asset_type_spine`).
- OBR (2025), [Costing of changes to the main, BADR and IR rates of capital gains tax](https://obr.uk/docs/dlm_uploads/CGT-supplementary-release-Jan-2025.pdf).
