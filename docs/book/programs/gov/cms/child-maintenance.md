# Child maintenance (planned)

```{warning}
**Not yet modelled in detail.** The model does not calculate a Child
Maintenance Service (CMS) award. This page sets out the scope for doing that,
tracked in [#669](https://github.com/PolicyEngine/policyengine-uk/issues/669)
(still open, October 2026).
```

## What the model does today

- `maintenance_income` holds child maintenance received. Datasets fill it
  from the Family Resources Survey child maintenance module.
- `spousal_maintenance_income` holds maintenance paid by a spouse, civil
  partner, former spouse or former civil partner
  ([#2572](https://github.com/PolicyEngine/policyengine-uk/issues/2572)).
- Both are added to `market_income`, `household_market_income` and
  `hbai_household_net_income`. `maintenance_expenses` (maintenance paid) is
  subtracted in `market_income` and `hbai_household_net_income`.
- Only `spousal_maintenance_income` feeds the means tests:
  - Universal Credit unearned income
    ([UC Regulations 2013 reg. 66(1)(d)](https://www.legislation.gov.uk/uksi/2013/376/regulation/66));
  - Pension Credit income
    ([State Pension Credit Regulations 2002 reg. 15(5)(d)](https://www.legislation.gov.uk/uksi/2002/1792/regulation/15)),
    but not savings credit qualifying income (reg. 9(f));
  - Housing Benefit income, less £15 a week where the family includes a child
    or young person
    ([HB Regulations 2006 Sch. 5 para. 47](https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/47);
    [HB (SPC) Regulations 2006 reg. 29(1)(o) and Sch. 5 para. 20](https://www.legislation.gov.uk/uksi/2006/214/regulation/29)).
- UC earned income does not net off maintenance paid.
- `uc_deductions` does cover child maintenance collected from a paying
  parent's UC award, but only in aggregate: it sits in the above-cap excess
  of `uc_deduction_rate` with last resort deductions, estimated from DWP
  deduction data rather than from `maintenance_expenses`.

For **child** maintenance that is the right answer for UC:

- **Receiving parent:** child maintenance is not unearned income under
  [UC Regulations 2013 reg. 66(1)](https://www.legislation.gov.uk/uksi/2013/376/regulation/66),
  so it is fully disregarded.
- **Paying parent:** maintenance paid is not deducted, so the paying parent is
  means-tested on their full earnings.

This asymmetry is the work-incentive problem described by the Centre for Social
Justice in [*The Hidden Parent Poverty Trap: Child Maintenance and Universal
Credit*][csj]. The model reproduces it, because neither child maintenance
variable reaches UC.

## Scope

### Phases 1 and 2: separate the inputs and count spousal maintenance

Done in the engine by #2572. What remains is in the data: datasets that put
the FRS payments from an absent partner in `private_transfer_income` should
move them to `spousal_maintenance_income`
([policyengine-uk-data#627](https://github.com/PolicyEngine/policyengine-uk-data/issues/627);
[Microcosm UK](https://github.com/PolicyEngine/microcosm)). Datasets that do
not supply it keep today's results.

### Phase 3: model the CMS calculation

Derive the CMS weekly amount when the inputs are available, from the paying
parent's gross weekly income
([GOV.UK](https://www.gov.uk/how-child-maintenance-is-worked-out);
[Child Support Act 1991 Sch. 1](https://www.legislation.gov.uk/ukpga/1991/48/schedule/1)):

| Paying parent's gross weekly income | Rate | Weekly amount |
|---|---|---|
| Below £7 | Nil | £0 |
| £7 to £100, or on benefits | Flat | £7 |
| £100.01 to £199.99 | Reduced | Formula |
| £200 to £3,000 | Basic | 12% / 16% / 19% of income up to £800 for 1 / 2 / 3+ children, then 9% / 12% / 15% of income from £800 to £3,000 |
| Above £3,000 | Basic, capped | Income above £3,000 is ignored; the receiving parent can apply to the courts |
| Not enough information | Default | £38 / £51 / £64 |

Then:

- **Shared care:** the amount falls by 1/7 for 52 to 103 nights a year, 2/7
  for 104 to 155, 3/7 for 156 to 174, and by half plus £7 a week for 175 or
  more.
- **Other children:** an adjustment applies for other children living with
  the paying parent.

The income bands are fixed in legislation, not uprated each year.

Phase 3 is optional for UC analysis, which needs only Phases 1 and 2. It
allows reforms to the CMS rates or bands to be scored.

## Implementation outline

### Parameters under `gov/cms/`

- `income_bands/`: the £7, £100, £200, £800 and £3,000 limits.
- `rate/flat.yaml`, `rate/default/` and `rate/basic/` (12/16/19% and
  9/12/15%).
- `rate/reduced/`: the reduced-rate formula.
- `shared_care/`: the night bands and fractions.

### Variables under `variables/gov/cms/`

- `child_maintenance_gross_weekly_income` (Person)
- `child_maintenance_obligation_pre_shared_care` (Person)
- `child_maintenance_shared_care_reduction` (Person)
- `child_maintenance_paid_cms_basis` (Person, derived award)

## Data needs

- **FRS** records maintenance received and paid at person level. Phase 1
  needs a check of how far its source items separate child maintenance
  from spousal maintenance.
- **DWP [Child Maintenance Service statistics][cms-stats]** (quarterly, latest
  data to June 2026) give the CMS caseload and amounts. They support checking
  the new inputs, bearing in mind that many families use private
  ("family-based") arrangements outside the CMS.

## References

- Centre for Social Justice, [The Hidden Parent Poverty Trap: Child
  Maintenance and Universal Credit][csj].
- GOV.UK, [How child maintenance is worked out](https://www.gov.uk/how-child-maintenance-is-worked-out).
- [Child Support Act 1991](https://www.legislation.gov.uk/ukpga/1991/48/contents) and [Schedule 1](https://www.legislation.gov.uk/ukpga/1991/48/schedule/1).
- [The Child Support Maintenance Calculation Regulations 2012 (SI 2012/2677)](https://www.legislation.gov.uk/uksi/2012/2677/contents).
- [The Universal Credit Regulations 2013, reg. 66](https://www.legislation.gov.uk/uksi/2013/376/regulation/66).
- DWP, [Child Maintenance Service statistics][cms-stats].

[csj]: https://www.centreforsocialjustice.org.uk/library/the-hidden-parent-poverty-trap-child-maintenance-and-universal-credit
[cms-stats]: https://www.gov.uk/government/collections/statistics-on-the-2012-statutory-child-maintenance-scheme
