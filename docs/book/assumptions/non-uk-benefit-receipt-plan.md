# Benefit expenditure paid outside UK private households (planned)

```{note}
**Planning page.** PolicyEngine UK calibrates household-level benefit
aggregates to **DWP/HMRC outturn totals** for the UK as a whole.
Some of that outturn doesn't go to **UK private households** — it
goes to people living abroad (exported pensions), people in
institutional accommodation outside the FRS sampling frame (care homes,
hostels), and a small administrative-leakage residual. This page
captures the proposed treatment, tracked under
[#842](https://github.com/PolicyEngine/policyengine-uk/issues/842).
```

## Why this matters

When we calibrate FRS-derived household weights so that simulated
`state_pension` matches OBR's £140bn total (say), we are implicitly
assuming every pound of OBR-reported expenditure lands on an FRS
household. It doesn't:

- **Exported State Pension** — UK pensioners living overseas receive
  basic / new State Pension at the rate they accrued. ~£5bn/yr by recent
  DWP statistics, paid to people the FRS doesn't sample.
- **Disability Living Allowance / PIP** abroad — limited cases under
  reciprocal agreements (EU/EFTA + a handful of others).
- **Institutional residents** — care-home residents receive most
  benefits but the FRS doesn't sample care homes. Their entitlements
  feed into the DWP outturn but not into PolicyEngine's `state_pension`
  totals.
- **Administrative leakage** — fraud / error / advance payments that
  appear in DWP cashflow but never reach an entitled person.

The current calibration absorbs all of the above into FRS-household
benefits, **inflating** PolicyEngine's per-household estimates by
whatever share of outturn actually lives outside UK private
households.

## Scope

### Phase 1 — quantify the gap by programme

For each benefit programme tracked in `programs.yaml`, identify the
share of outturn that goes outside UK private households. DWP and HMRC
publish enough data to assemble a first-pass table:

| Programme | UK private households | Overseas | Institutional | Admin / error |
|-----------|----------------------|----------|---------------|---------------|
| State Pension | published | DWP overseas tables | -- | -- |
| Pension Credit | published | small | minimal | minor |
| Universal Credit | published | minimal | small | F&E published |
| Housing Benefit | published | -- | care-home component | F&E published |
| Child Benefit | published | EU-treaty residue | -- | -- |
| Disability Living Allowance / PIP | published | reciprocal residue | -- | -- |
| Attendance Allowance | published | -- | care-home residue | -- |
| Winter Fuel Payment | published | overseas eligible cohort | -- | -- |

Sources: DWP *Benefits paid outside the United Kingdom* statistics, the
DWP *Fraud and Error in the Benefit System* annual release, and
programme-specific outturn breakdowns.

### Phase 2 — subtract from calibration targets

Once the gap is quantified per programme, the **calibration target** in
`policyengine-uk-data` should be the **UK-private-household component**
of outturn, not the full outturn. Concretely:

- Add a column `private_household_share` (0–1) to each programme's
  calibration target row, default 1.0 with explicit per-programme
  overrides.
- Update the reweighting loss function to compare simulated household
  aggregates against `outturn × private_household_share` rather than
  raw outturn.

This avoids the overweighting bias without trying to synthesise
out-of-scope households.

### Phase 3 — explicit out-of-scope synthesis (optional)

For headline aggregates that need to match the **full** outturn (e.g.
fiscal cost of a reform), maintain an out-of-scope additive correction
per programme rather than synthesising fake households. This is
preferable because:

- Distributional analyses already get the right answer at Phase 2 (UK
  private households are correctly weighted to their own outturn).
- Synthesising overseas / institutional households would require strong
  assumptions about their characteristics that aren't validated against
  any micro-data source.

The additive correction lives in `policyengine-uk-data` and surfaces in
PolicyEngine UK as an explicit non-household revenue / spending line.

## Implementation outline

This is primarily a **data-side** change in `policyengine-uk-data`. The
in-repo changes are minor:

- A new `private_household_share` field on each row of
  [`programs.yaml`](../../../policyengine_uk/programs.yaml) (default 1.0
  for everything but State Pension, AA, and a handful of others).
- A documentation hook from the calibrated programme variables back to
  this page so the modelling assumption is discoverable.

## Open questions

- Should the `private_household_share` be year-varying (e.g. overseas
  State Pension share rose post-EU exit) or held flat?
- For Universal Credit, where the FRS *does* sample some
  institutionalised people (in supported accommodation), what's the
  correct private-household-share value — strictly < 1, or 1 minus a
  smaller residual?
- For the household-calculator (single-household) interface, the
  private-household-share correction shouldn't apply — the user
  represents their own household. Confirm the correction is only on the
  microsim weighted aggregates.

## References

- DWP, [Benefits paid outside the United Kingdom statistics](https://www.gov.uk/government/collections/benefits-paid-outside-the-united-kingdom) — overseas residue by programme.
- DWP, [Fraud and Error in the Benefit System](https://www.gov.uk/government/collections/fraud-and-error-in-the-benefit-system) — administrative leakage estimates.
- DWP, [Stat-Xplore](https://stat-xplore.dwp.gov.uk/) — programme-specific caseload breakdowns including residence and tenure splits.
- HMRC, [Tax credits and Child Benefit statistics](https://www.gov.uk/government/collections/personal-tax-credits-statistics) — EU-treaty Child Benefit residue.
- Issue: [#842](https://github.com/PolicyEngine/policyengine-uk/issues/842). Related: [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621) (UK pipeline alignment).
