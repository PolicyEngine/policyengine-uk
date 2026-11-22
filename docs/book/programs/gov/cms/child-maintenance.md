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
- `spousal_maintenance_income` counts as the claimant's or partner's income
  in these means tests:
  - Universal Credit unearned income
    ([UC Regulations 2013 reg. 66(1)(d)](https://www.legislation.gov.uk/uksi/2013/376/regulation/66));
  - Pension Credit income
    ([State Pension Credit Regulations 2002 reg. 15(5)(d)](https://www.legislation.gov.uk/uksi/2002/1792/regulation/15)),
    but not savings credit qualifying income (reg. 9(f));
  - Income Support income, in full, as a liable relative payment
    ([IS Regulations 1987 regs. 54 to 58](https://www.legislation.gov.uk/uksi/1987/1967/part/V/chapter/VII));
  - Housing Benefit income, less £15 a week where the family includes a child
    or young person
    ([HB Regulations 2006 Sch. 5 para. 47](https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/47);
    [HB (SPC) Regulations 2006 reg. 29(1)(o)](https://www.legislation.gov.uk/uksi/2006/214/regulation/29)
    and [Sch. 5 para. 20](https://www.legislation.gov.uk/uksi/2006/214/schedule/5/paragraph/20));
  - Council Tax Reduction income, also less £15 a week where the family
    includes a child or young person
    ([SI 2012/2885 Sch. 5 para. 20](https://www.legislation.gov.uk/uksi/2012/2885/schedule/5/paragraph/20)
    sets this for pension-age applicants in England). For working-age
    applicants with Universal Credit, the model counts it in full in the
    five English council schemes it holds and in Wales: Wales, Merton,
    Kingston upon Thames, Newham and Westminster count it through the
    Universal Credit income figure, and Oxford, from April 2026, as other
    unearned income under its Appendix 3. Applicants without Universal
    Credit in those five schemes, and Oxford's with it before April 2026,
    have the same £15 disregard. Elsewhere in England the model uses a
    working-age applicant's reported reduction, so their income does not
    count. It caps the report at their share of a jointly liable bill when
    another claim in the household is paid a simulated reduction and no one
    counted in the share may be a student. The
    model leaves spousal maintenance out of Scotland's working-age scheme,
    and out of the Welsh one for applicants without Universal Credit,
    although both count it less £15 a week: Scotland where the family
    includes a child or young person, Wales where the applicable amount
    includes a family premium
    ([SSI 2021/249 reg. 57(1)(d) and (6)](https://www.legislation.gov.uk/ssi/2021/249/regulation/57);
    [WSI 2013/3029 Sch. 6 para. 17](https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/17)
    and [Sch. 9 para. 49](https://www.legislation.gov.uk/wsi/2013/3029/schedule/9/paragraph/49)).
    [#2931](https://github.com/PolicyEngine/policyengine-uk/issues/2931) tracks the fix.
- `maintenance_income` counts in none of those, except in Oxford City
  Council's Council Tax Reduction scheme for Universal Credit applicants
  from April 2026.
- Both count towards the Childcare Offer for Wales income limit
  ([Welsh Government, Assessing parents' income, question 9](https://www.gov.wales/sites/default/files/publications/2023-04/atisn17333doc1.pdf#page=7);
  [guidance for local authorities, para. 69](https://www.gov.wales/sites/default/files/publications/2026-04/childcare-offer-for-wales-guidance-for-local-authorities-april-2026-english_0.pdf#page=18)).
  Both also count in a non-dependant's gross income for the Housing Benefit
  non-dependant deduction, and for the Council Tax Reduction one in the
  English pension-age, Scottish and Welsh schemes; the five English council
  schemes count only spousal maintenance there. Neither the Housing Benefit
  list nor the English pension-age list of non-dependant income disregards
  covers maintenance
  ([HB Regulations 2006 reg. 74(9)](https://www.legislation.gov.uk/uksi/2006/213/regulation/74);
  [SI 2012/2885 Sch. 1 para. 8(9)](https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8)).
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

The paying-parent side of this asymmetry is the work-incentive problem
described by the Centre for Social Justice in [*The Hidden Parent Poverty Trap:
Child Maintenance and Universal Credit*][csj]. The model reproduces UC's side
of it, because neither child maintenance variable reaches UC. It does not
reproduce the combined marginal rates, because `maintenance_expenses` is a
fixed input that does not rise with earnings.

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
| Not enough information | Default | £39 / £51 / £64 ([SI 2012/2677 reg. 49](https://www.legislation.gov.uk/uksi/2012/2677/regulation/49); GOV.UK's guide shows £38 for one child) |

Then:

- **Shared care:** for the basic and reduced rates, the amount payable to
  each carer falls by 1/7 where a child spends 52 to 103 nights a year with
  the paying parent, 2/7 for 104 to 155, 3/7 for 156 to 174 and 1/2 for 175
  or more; where one carer looks after more than one qualifying child, the
  fractions for those children are added and divided by the number of them
  (para. 7(5)). It then falls
  by a further £7 a week for each child with 175 or more nights, but not
  below £7 a week in total (Sch. 1 para. 7). Where the flat rate applies
  because the paying parent or their partner gets a prescribed benefit
  (para. 4(1)(b) or (c) or 4(2)), 52 or more nights with a child makes the
  amount payable to that child's carer nil (para. 8).
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
