# Capital gains distribution

```{note}
**Planning page, updated October 2026.** Tracks
[#818](https://github.com/PolicyEngine/policyengine-uk/issues/818)
(model gains jointly across income groups) and
[#817](https://github.com/PolicyEngine/policyengine-uk/issues/817)
(don't impute gains to households with no wealth). The imputation lives
in the data pipeline, not in this repo. Most of what this page proposed
in May 2026 has since been built in
[Microcosm UK](https://github.com/PolicyEngine/microcosm), which is now
the UK data pipeline. What remains is listed at the
end of this page.
```

## How the model uses capital gains

`capital_gains_before_response` is a person-level input, uprated by OBR
per-capita GDP growth. `capital_gains_tax` charges it at the main CGT
rates, with three components charged at their own rates (all added by
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
rate. Gains qualifying for BADR respond at their own elasticity
(`capital_gains_badr_elasticity`); the rest use
`gov.simulation.capital_gains_responses.elasticity`.

## How the gains are imputed

### Before: one distribution per income decile

The Enhanced FRS fitted a separate gains distribution within each
income decile and drew each household's gains from its decile. #818
pointed out the problems:

- each decile's upper tail was fitted on few observations, so the tails
  were noisy and the joint distribution of income and gains had breaks
  at decile boundaries;
- two people in the same decile drew from the same distribution however
  different their incomes;
- gains depended on income only, not on wealth, so they could be
  imputed to households with no assets (#817).

### Now: Microcosm UK

Microcosm builds gains in four stages (see the UK
[sources specification](https://github.com/PolicyEngine/microcosm/blob/75167a68/packages/microcosm-build/src/microcosm/build/uk/spec/sources.yaml)):

1. **Support split** (`cgt_support_split`). Within each income band of
   HMRC Capital Gains Tax statistics Table 3, the households with the
   most investable wealth (financial wealth, business wealth and
   property other than the main home) are split into lighter copies, so
   that there are enough rows to hold the largest gains.
2. **Who has gains** (`cgt_incidence_clone`). The set and order of
   gainers come from the incidence distribution in Advani and Summers
   (2020), *Capital Gains and UK Inequality* (CAGE Working Paper 465).
3. **How much** (`hmrc_cgt_gains_spine`). Amounts are redrawn so that
   gains match HMRC Table 3 for 2024-25, which counts taxpayers and
   gains **jointly by size of gain and taxable income**, conditioned on
   Tables 1, 2.1a, 5 and 6.
4. **What kind** (`hmrc_cgt_asset_type_spine`). Gains are split by
   asset type using Table 8 (residential property), Table 4.1 (BADR and
   Investors' Relief) and Table 7 (gains by asset type), which fills
   `capital_gains_residential_property` and `capital_gains_badr`.

All the HMRC tables come from the Capital Gains Tax statistics July
2026 release, through Microcosm's pinned Chronicle feed.

Against #818: gains are now fitted to the published joint distribution
of gain size and taxable income, not decile by decile. Against #817:
the largest gains are placed on the wealthiest households in each
income band. Microcosm's release checks also include a projection check
on people just below the annual exempt amount (`gates.json`), so that
uprating does not push implausible numbers of them into paying CGT in
later years.

## What's left

- **A zero-wealth test.** Add a test, here or in Microcosm, that no
  positive gains sit on households with zero investable wealth. Neither
  repo asserts this directly yet, so #817 should stay open until it
  does.
- **Close #818** once the next certified Microcosm release confirms the
  Table 3 fit, and link the release's diagnostics from the issue.
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
- Microcosm UK [sources specification](https://github.com/PolicyEngine/microcosm/blob/75167a68/packages/microcosm-build/src/microcosm/build/uk/spec/sources.yaml) (stages `cgt_support_split`, `cgt_incidence_clone`, `hmrc_cgt_gains_spine`, `hmrc_cgt_asset_type_spine`).
