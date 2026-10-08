# Benefit expenditure paid outside UK private households (planned)

```{note}
**Planning page.** The data behind PolicyEngine UK is calibrated so that
household benefit totals match published **DWP/HMRC/OBR totals**.
Some of that outturn doesn't go to **UK private households** — it
goes to people living abroad (exported pensions), people in
institutional accommodation outside the FRS sampling frame (care homes,
hostels), and a small administrative-leakage residual. This page
sets out the proposed treatment, tracked in
[#842](https://github.com/PolicyEngine/policyengine-uk/issues/842) (still
open, October 2026). Calibration now happens in
[Microcosm UK](https://github.com/PolicyEngine/microcosm), which replaced
the Enhanced FRS build, so most of the work below belongs there.
```

## Why this matters

Calibrating FRS household weights so that simulated `state_pension`
matches a national spending total assumes every pound of that total lands
on a household the FRS samples. It doesn't:

- **State Pension paid abroad** — pensioners living overseas receive the
  State Pension they built up. DWP's benefit expenditure tables report
  the amount paid to recipients abroad, and Stat-Xplore gives the
  caseload by country. None of these people are in the FRS.
- **Disability Living Allowance / PIP** abroad — limited cases under
  reciprocal agreements (EU/EFTA + a handful of others).
- **Institutional residents** — care-home residents receive most
  benefits but the FRS doesn't sample care homes. Their entitlements
  feed into the DWP outturn but not into PolicyEngine's `state_pension`
  totals.
- **Administrative leakage** — fraud / error / advance payments that
  appear in DWP cashflow but never reach an entitled person.

Where a target includes these groups, calibration pushes their spending
onto FRS households and **overstates** what UK private households receive.

**Already done for State Pension.** Microcosm no longer fits the OBR State
Pension forecast, which counts Great Britain plus pensioners paid abroad and
leaves out Northern Ireland. State Pension is now bound to the resident
figures from DWP Stat-Xplore and the Northern Ireland Department for
Communities. That ruling (R4) is recorded under
[microcosm#1069](https://github.com/PolicyEngine/microcosm/issues/1069).
The same question is open for other programmes.

## Scope

### Phase 1 — quantify the gap by programme

For each benefit programme the calibration targets, identify the share
of the published total that goes outside UK private households. DWP and HMRC
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

Sources: DWP *Benefit expenditure and caseload tables* and Stat-Xplore
(payments abroad), the DWP *Fraud and Error in the Benefit System* annual
release, and programme-specific breakdowns.

### Phase 2 — subtract from calibration targets

Once the gap is quantified per programme, each **calibration target**
should be the **UK-private-household part** of the total, not the full
total. Microcosm's State Pension change does this by binding a resident
series instead. Where no resident series exists, the target can carry an
explicit private-household share (0–1, default 1) with a cited source for
each override.

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

The additive correction would live in the data pipeline and appear in
PolicyEngine UK as an explicit non-household spending line.

## Implementation outline

This is mainly a **data-side** change in Microcosm UK's target
register. (`policyengine_uk/programs.yaml` is metadata on model coverage,
not calibration targets, so it is not the place for these shares.) The
changes in this repo are small:

- a non-household spending line for the Phase 3 correction, if adopted;
- documentation linking the affected benefit variables to this page.

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

- DWP, [Benefit expenditure and caseload tables](https://www.gov.uk/government/collections/benefit-expenditure-and-caseload-tables) — spending by benefit, including payments abroad.
- DWP, [Fraud and Error in the Benefit System](https://www.gov.uk/government/collections/fraud-and-error-in-the-benefit-system) — administrative leakage estimates.
- DWP, [Stat-Xplore](https://stat-xplore.dwp.gov.uk/) — caseloads by benefit, including State Pension recipients by country of residence.
- HMRC, [Tax credits and Child Benefit statistics](https://www.gov.uk/government/collections/personal-tax-credits-statistics) — EU-treaty Child Benefit residue.
- Issue: [#842](https://github.com/PolicyEngine/policyengine-uk/issues/842). Related: [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621) (UK pipeline alignment) and [microcosm#1069](https://github.com/PolicyEngine/microcosm/issues/1069) (State Pension on resident figures).
