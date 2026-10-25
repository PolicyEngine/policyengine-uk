# Housing Benefit family-premium test coverage

The property tests in `test_housing_benefit_family_premium_properties.py` cover
seven contracts: addition to the applicable amount, one premium per family,
no premium without a legally included child, the annual closure/category
rule, the historical lone-parent routing grid, the three supported amounts,
and an independent Northern Ireland closure-date reform.

The property tests use declared parameter amounts as structural oracles.
Their 2027–2030 cases cover projections and parameter relationships; they do
not certify future legislation or published future rates. The range assertion
does not order the two positive amounts: the ordinary amount is uprated and
the historical amount has no uprating metadata. Category and regime grid
cells test input routing, rather than adjudicating continuous protection.
Historical higher-rate cells do not add an ESA-component premise, which the
saved entitlement conditions exclude.

The general identity is `A(category) - A(NONE) = F(category) - F(NONE)`.
The stronger equality to `F(category)` applies only from the closure year.
In 2015, an included child gives the ordinary premium even with category
NONE, so ordinary-minus-NONE is zero while each premium is £907.40. The
annual model applies each closure date's year; it does not reconstruct claim
changes within 2016. The NI scenario moving closure to September 2017 is a
counterfactual branch test and leaves GB and both amount parameters alone.

Four full-person YAML fixtures use a male claimant aged 75 and a dependent
child aged 15 in 2026, in GB and NI and in both person orders. Explicit roles
and the parent's relationship fact distinguish the claimant from the child.
The eldest age, pension-age date, pension-regime result and pre-April 2021
cohort flag are derived, rather than supplied. An independently pre-assessed
continuing protected award is a premise; ages alone do not establish it.
The fixed component oracle is £256×52 + £20.22×52 = **£14,363.44**.
The NI case checks the existing shared UK age-date API with its own HB cohort
rates, without newly certifying separate NI pension-age enactments.

A separate 2015 working-age fixture has five positive components:

| Component | Annual amount |
|---|---:|
| Younger lone-parent allowance, £57.90×52 | £3,010.80 |
| Pre-assessed carer premium, £34.60×52 | £1,799.20 |
| Ordinary family premium, £17.45×52 | £907.40 |
| Ordinary disabled-child premium, £60.06×52 | £3,123.12 |
| Main-phase ESA difference, (£73.10−£57.90)×52 | £790.40 |
| Applicable amount | **£9,630.92** |

That fixture uses a 17-year-old lone parent before new-claim closure. It does
not invent protected continuity for a teenager in 2026 or combine historical
higher lone-parent protection with an ESA component. The carer term is
lawfully pre-assessed, including qualifying care and entitlement/overlap
facts. The test supplies it directly and does not test adult-premium priority
or carer's allowance eligibility. Positive DLA/PIP receipt sentinels in these
component tests are predicates, rather than certified award amounts. Enhanced
child triggers remain false where the ordinary-only child amount is expected.
Personal allowance plus the ESA adjustment is £73.10/week, not two full
personal allowances. These fixtures test selected component sums, not a
complete HB/ESA/carer award, dataset or population result.

Primary references:

- [GB closure and savings](https://www.legislation.gov.uk/uksi/2015/1857/made)
  and [NI closure and savings](https://www.legislation.gov.uk/nisr/2016/310/made).
- [Saved GB family rules](https://www.legislation.gov.uk/uksi/2006/213/schedule/3/part/2/2015-04-06)
  and [saved NI family rules](https://www.legislation.gov.uk/nisr/2006/405/schedule/4/part/II/2015-04-06).
- [2015 personal allowances](https://www.legislation.gov.uk/uksi/2006/213/schedule/3/part/1/2015-04-06),
  [family rates](https://www.legislation.gov.uk/uksi/2015/457/article/17/made)
  and [other premium rates](https://www.legislation.gov.uk/uksi/2015/457/schedule/6/made).
- [DWP 2026–27 rates](https://www.gov.uk/government/publications/benefit-and-pension-rates-2026-to-2027/proposed-benefit-and-pension-rates-2026-to-2027),
  [GB pension-age schedule](https://www.legislation.gov.uk/uksi/2006/214/schedule/3),
  [NI pension-age schedule](https://www.legislation.gov.uk/nisr/2006/406/schedule/4)
  and [Pensions Act 1995 Schedule 4](https://www.legislation.gov.uk/ukpga/1995/26/schedule/4).
