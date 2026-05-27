# Child maintenance (planned)

```{warning}
**Not yet modelled in detail.** PolicyEngine UK currently has two generic
input variables — `maintenance_income` and `maintenance_expenses` — that
flow through HBAI but do **not** distinguish child maintenance from
other maintenance and do **not** apply the Universal Credit asymmetry
described below. This page captures the agreed scope for adding a
properly-modelled Child Maintenance Service (CMS) calculation, tracked
under [#669](https://github.com/PolicyEngine/policyengine-uk/issues/669).
```

## Why model child maintenance separately

The Centre for Social Justice paper [*The Hidden Parent Poverty Trap:
Child Maintenance and Universal Credit*][csj] shows that the
**asymmetric** UC treatment of child maintenance produces a meaningful
work-incentive cliff for paying parents:

- **Receiving parent**: child maintenance income is **fully disregarded**
  in the UC means test. That's good for the receiving household and
  matches the policy intent of CMS.
- **Paying parent**: child maintenance paid out is **not** deducted from
  earnings in the UC means test. The paying parent is means-tested on
  gross earnings as if the maintenance had never left their pocket.

The current PolicyEngine treatment uses a single `market_income`
deduction `income - maintenance_expenses` (`variables/household/income/
market_income.py`). That is fine for HBAI net income but is **too
generous** to the paying parent in UC — they would currently see
maintenance reduce their UC-applicable income too, producing higher UC
than they actually get.

## Scope

### Phase 1 — disambiguate the inputs

- New input variable `child_maintenance_received` (Person, GBP, annual)
  — the amount of CMS / private child maintenance the person receives.
- New input variable `child_maintenance_paid` (Person, GBP, annual) —
  the amount the person pays out.
- Keep `maintenance_income` / `maintenance_expenses` for spousal and
  other maintenance flows; document the distinction explicitly.
- In `policyengine-uk-data`, route the FRS child-maintenance items into
  the new variables and the FRS spousal-maintenance items into the
  existing ones.

### Phase 2 — fix the UC asymmetry

- New variable `uc_applicable_child_maintenance` (BenUnit) that returns
  **`child_maintenance_received` only**, with `child_maintenance_paid`
  set to **zero** — i.e. the UC-side asymmetry.
- Subtract `uc_applicable_child_maintenance` from
  `uc_applicable_income` so it's fully disregarded for the receiver.
- Crucially **do not** subtract `child_maintenance_paid` from
  `uc_applicable_income`; this reproduces the CSJ-identified poverty
  trap.

### Phase 3 — model the CMS formula itself

Currently both `maintenance_income` and the proposed `child_maintenance_*`
variables are pure inputs. Phase 3 would derive the CMS award when the
required inputs are present, using the gross-income basis the CMS
applies:

| Paying-parent gross weekly income | Rule |
|------------------------------------|------|
| Less than £7  | No payment ("nil rate") |
| £7 – £100     | Flat-rate £7 |
| £100 – £200   | Reduced rate (formula-based) |
| £200 – £3,000 | Basic rate: 12% / 16% / 19% of gross income for 1 / 2 / 3+ children, with a tapered top slice between £800 and £3,000 |
| Over £3,000   | Capped at the £3,000 figure (statutory upper limit) |

Plus the **shared-care reduction** (one-seventh per night of shared
care up to 174 nights/year) and the **other-children adjustment** for
non-qualifying children living with the paying parent.

Phase 3 is optional for headline UC analysis (where the asymmetry in
Phase 2 is what matters) but unlocks reform scenarios that change the
CMS rate or threshold.

## Implementation outline

### New parameters under `gov/cms/`

- `gross_income_band/{lower,upper}_threshold.yaml` (£7 and £3,000 weekly
  in 2025 terms)
- `rate/basic/{1,2,3_or_more}_child.yaml` (12 / 16 / 19%)
- `rate/reduced/{base,marginal}.yaml`
- `shared_care/reduction_per_night.yaml`
- `take_up/cms_collect_share.yaml` (HMRC published share of CMS-vs-
  family-arrangement maintenance)

### New variables under `variables/gov/cms/`

- `child_maintenance_gross_weekly_income` (Person)
- `child_maintenance_obligation_pre_shared_care` (Person)
- `child_maintenance_shared_care_reduction` (Person)
- `child_maintenance_paid_cms_basis` (Person, derived award)

### UC integration

- `variables/gov/dwp/universal_credit/uc_applicable_income.py` adds
  `child_maintenance_received` as a deduction (full disregard) and
  **does not** deduct `child_maintenance_paid` — matching the policy.
- HBAI keeps the current symmetric treatment; the CSJ asymmetry is a
  UC-side specific.

## Data needs

- **FRS** records both receipt and payment of maintenance and identifies
  the recipient/payer at person level. Phase 1 imputation routes FRS
  child-maintenance items into the new variables.
- **CMS / Child Maintenance Statistics** ([gov.uk/government/collections/
  child-maintenance-service-statistics][cms-stats]) give published
  CMS-arrangement caseload and total maintenance flowing through the
  statutory scheme; useful for calibrating the new variables against
  the share of maintenance that goes through CMS vs. private
  ("family-based") arrangements.

## References

- Centre for Social Justice, [The Hidden Parent Poverty Trap: Child
  Maintenance and Universal Credit][csj].
- DWP, [How we work out child maintenance][how-we-work-out] — official
  user-facing CMS methodology guide.
- [Child Support Act 1991](https://www.legislation.gov.uk/ukpga/1991/48/contents) — primary statute.
- [The Child Support Maintenance Calculation Regulations 2012 (SI 2012/2677)](https://www.legislation.gov.uk/uksi/2012/2677/contents) — the operational regulations.
- HMRC/DWP, [Child Maintenance Service statistics][cms-stats] — caseload and expenditure outturns.

[csj]: https://www.centreforsocialjustice.org.uk/library/the-hidden-parent-poverty-trap-child-maintenance-and-universal-credit
[how-we-work-out]: https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/672432/how-we-work-out-child-maintenance.pdf
[cms-stats]: https://www.gov.uk/government/collections/child-maintenance-service-statistics
