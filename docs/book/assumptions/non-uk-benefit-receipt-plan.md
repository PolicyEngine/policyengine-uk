# Benefit expenditure paid outside UK private households (planned)

```{note}
**Planning page.** The data behind PolicyEngine UK is calibrated so that
household benefit totals match published **DWP/HMRC/OBR totals**.
Some of that outturn doesn't go to **UK private households**. It
goes to people living abroad (exported pensions) and to people in
institutional accommodation outside the FRS sampling frame (care homes,
hostels). Fraud and error overpayments are a separate issue: claimants
receive them but aren't entitled to them. This page
sets out the proposed treatment, tracked in
[#842](https://github.com/PolicyEngine/policyengine-uk/issues/842) (still
open, October 2026). Microcosm UK, the dataset in policyengine.py's
certified UK bundle, sets its calibration targets in
[Microcosm](https://github.com/PolicyEngine/microcosm), so most of the work
below belongs there. policyengine-uk-data's Enhanced FRS, which this
repository's microsimulation test jobs and aggregate-impact report still run
on, keeps its own target set, which still includes the OBR State Pension
line.
```

## Why this matters

Calibrating FRS household weights so that simulated `state_pension`
matches a national spending total assumes every pound of that total lands
on a household the FRS samples. It doesn't:

- **State Pension paid abroad**: pensioners living overseas receive the
  State Pension they built up. DWP's benefit expenditure tables report
  the amount paid to recipients abroad, and Stat-Xplore gives the
  caseload by country. None of these people are in the FRS.
- **Disability and carer benefits paid abroad**: limited cases. The DLA care
  component, the PIP daily living part, Attendance Allowance and Carer's
  Allowance can be paid to people living in an EEA country or Switzerland
  who are covered by the Withdrawal Agreement; the mobility parts can't be
  paid abroad. DWP's tables report each benefit's spending outside the UK.
- **Institutional residents**: care-home residents keep their State
  Pension and can get some other benefits (Pension Credit, or Attendance
  Allowance if they pay for their own care), but the FRS doesn't sample
  care homes. Their entitlements
  feed into the DWP outturn but not into PolicyEngine's `state_pension`
  totals.

Where a target includes these groups, calibration pushes their spending
onto FRS households and **overstates** what UK private households receive.

**Fraud and error** is a different case. DWP counts overpayments as benefit
spending although they go beyond what claimants are entitled to: 3.2% of
benefit spending in its FYE 2026 estimates, against 0.4% underpaid through
official error. That
money does reach households, so it doesn't overstate what they receive, but
it matters where the model simulates entitlement rather than receipt.

**Already done for State Pension paid abroad.** Microcosm no longer binds the OBR State
Pension line. State Pension is now bound to resident figures from DWP
Stat-Xplore (Great Britain) and the Northern Ireland Department for
Communities, and the OBR line and DWP's "paid outside UK" line are kept as
diagnostics. The plan began as
[microcosm#1069](https://github.com/PolicyEngine/microcosm/issues/1069), which
now tracks the open follow-ups, and the change landed in
[microcosm#1084](https://github.com/PolicyEngine/microcosm/pull/1084)
(merged 2 October 2026). The resident series still includes care-home
residents. The same question is open for other programmes.

## Scope

### Phase 1: quantify the gap by programme

For each benefit programme the calibration targets, identify the share
of the published total that goes outside UK private households. DWP and HMRC
publish enough data to assemble a first-pass table. The fraud and error
column is recorded separately: that money reaches households, so it isn't
part of the gap.

| Programme | Published total | Overseas | Institutional | Fraud and error |
|-----------|-----------------|----------|---------------|-----------------|
| State Pension | published | DWP "paid outside UK" line | care-home residents | F&E published |
| Pension Credit | published | small (Great Britain residence required) | care-home residents (unquantified) | F&E published |
| Universal Credit | published | minimal | small | F&E published |
| Housing Benefit | published | -- | hostels (Housing Benefit doesn't pay for a care-home place) | F&E published |
| Child Benefit | published | EEA, Switzerland and agreement-country residue | -- | F&E published (HMRC annual report and accounts) |
| Disability Living Allowance / PIP | published | DWP "outside UK" lines | care-home residue (self-funders; both mobility parts) | F&E published |
| Attendance Allowance | published | DWP "outside UK" line | care-home residue (self-funders) | F&E published |
| Winter Fuel Payment | published | none since winter 2025-26 (recipients must be ordinarily resident in England, Wales or Northern Ireland) | care-home residents | -- |

Sources: DWP *Benefit expenditure and caseload tables* and Stat-Xplore
(payments abroad), the DWP *Fraud and Error in the Benefit System* annual
release, HMRC's annual report and accounts (Child Benefit fraud and error),
programme-specific breakdowns, and the rules on care homes
([Housing Benefit Regulations 2006 reg. 9(1)(k) and (4)](https://www.legislation.gov.uk/uksi/2006/213/regulation/9)
and the [pension-age equivalent](https://www.legislation.gov.uk/uksi/2006/214/regulation/9);
[PIP Regulations 2013 reg. 28](https://www.legislation.gov.uk/uksi/2013/377/regulation/28);
[DLA Regulations 1991 reg. 9](https://www.legislation.gov.uk/uksi/1991/2890/regulation/9))
and on Winter Fuel Payment residence
([SI 2025/969 reg. 2](https://www.legislation.gov.uk/uksi/2025/969/regulation/2)
for England and Wales;
[SR 2025/142 reg. 2](https://www.legislation.gov.uk/nisr/2025/142/regulation/2)
for Northern Ireland).

### Phase 2: subtract from calibration targets

Once the gap is quantified per programme, each **calibration target**
should be the **UK-private-household part** of the total, not the full
total. Microcosm's State Pension change does this for pensions paid abroad
by binding a resident series instead; that series still includes care-home
residents. Where no resident series exists, the target can carry an
explicit private-household share (0–1, default 1) with a cited source for
each override.

This avoids the overweighting bias without trying to synthesise
out-of-scope households.

### Phase 3: explicit out-of-scope correction (optional)

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

- Should the `private_household_share` be year-varying (e.g. the overseas
  share of State Pension spending was 4.3% in 2019-20 and 3.9% in 2024-25 in
  DWP's outturn tables) or held flat?
- For Universal Credit, if the FRS samples some people in supported
  accommodation, what's the correct private-household-share value:
  strictly < 1, or 1 minus a smaller residual?
- For the household-calculator (single-household) interface, the
  private-household-share correction shouldn't apply, because the user
  represents their own household. Confirm the correction is only on the
  microsim weighted aggregates.

## References

- DWP, [Benefit expenditure and caseload tables](https://www.gov.uk/government/collections/benefit-expenditure-and-caseload-tables): spending by benefit, including payments abroad.
- DWP, [Fraud and Error in the Benefit System](https://www.gov.uk/government/collections/fraud-and-error-in-the-benefit-system): estimates of benefit overpaid through fraud and error and underpaid through official error.
- DWP, [Stat-Xplore](https://stat-xplore.dwp.gov.uk/): caseloads by benefit, including State Pension recipients by country of residence.
- HMRC, [Annual reports and accounts](https://www.gov.uk/government/collections/hmrcs-annual-report-and-accounts): Child Benefit error and fraud estimates.
- GOV.UK, [Child Benefit if you leave the UK](https://www.gov.uk/child-benefit-abroad): when Child Benefit is paid for families abroad (EEA, Switzerland and social security agreement countries).
- Issue: [#842](https://github.com/PolicyEngine/policyengine-uk/issues/842). Related: [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621) (UK pipeline alignment) and [microcosm#1069](https://github.com/PolicyEngine/microcosm/issues/1069) (UK pensions follow-ups after #1084).
