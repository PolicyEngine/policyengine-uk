# Warm Home Discount (planned)

```{warning}
**Not yet modelled.** The Warm Home Discount (WHD) is a £150 rebate off
a household's electricity bill each winter, paid by energy suppliers
under schemes that Ofgem administers. PolicyEngine UK doesn't model it;
draft [#2504](https://github.com/PolicyEngine/policyengine-uk/pull/2504)
implements Phase 1 below.
This page sets out the proposed scope, tracked in
[#502](https://github.com/PolicyEngine/policyengine-uk/issues/502).
Updated October 2026: in England and Wales eligibility is now based on
benefit receipt alone, which makes the scheme much easier to model than
when this page was first drafted.
```

## The scheme now

### England and Wales

[The Warm Home Discount (England and Wales) Regulations 2026](https://www.legislation.gov.uk/uksi/2026/389/contents)
(SI 2026/389) continue the scheme from 1 April 2026 to 31 March 2031.
They replace the
[2022 Regulations](https://www.legislation.gov.uk/uksi/2022/772/contents)
(SI 2022/772), which applied to both England and Wales.

Under the eligibility statements made under the 2022 Regulations, the
means-tested group (Core Group 2) had to pass a "high cost to heat" test
based on property data. For winter 2025-26 the eligibility statement
removed that test, so every household on a qualifying means-tested
benefit became eligible. The government estimated this would bring
2.7 million more households into the scheme
([government response, June 2025](https://assets.publishing.service.gov.uk/media/6852e6e9679778c74ec15e82/expanding-the-warm-home-discount-scheme-2025-to-2026-government-response.pdf)),
taking it to around 6.1 million households in Great Britain
([impact assessment](https://assets.publishing.service.gov.uk/media/68529908ff16d05c5e6aa678/expanding-the-warm-home-discount-scheme-2025-to-2026-impact-assessment.pdf)).
For winter 2025-26 (qualifying date 24 August 2025) the qualifying
benefits also included income-based Jobseeker's Allowance and Income
Support, with Pension Credit Guarantee Credit in a separate core group
([eligibility statement, 2025 to 2026](https://www.gov.uk/government/publications/warm-home-discount-eligibility-statement-england-and-wales-2025-to-2026-scheme-year/warm-home-discount-eligibility-statement-england-and-wales-2025-to-2026)).

For winter 2026-27, GOV.UK
([eligibility in England and Wales](https://www.gov.uk/the-warm-home-discount-scheme/if-you-live-in-england-and-wales))
says a household qualifies if, on the qualifying date of 23 August
2026, its electricity supplier is in the scheme, the person's (or
their partner's) name is on the electricity bill, and the person or
their partner gets one of:

- Universal Credit;
- Housing Benefit;
- income-related Employment and Support Allowance;
- Pension Credit.

Most eligible households get the rebate automatically through data
matching; the rest are sent a letter and must call the helpline by
26 February 2027 to confirm their details.

### Scotland

The scheme runs under separate Scottish regulations.
[The Warm Home Discount (Scotland) Regulations 2026](https://www.legislation.gov.uk/uksi/2026/488/contents)
(SI 2026/488) came into force on 1 May 2026 and run the scheme to
31 March 2031, replacing the
[2022 Regulations](https://www.legislation.gov.uk/uksi/2022/1073/contents)
(SI 2022/1073). Both 2026 Regulations set the rebate at £150. For winter 2026-27
([eligibility in Scotland](https://www.gov.uk/the-warm-home-discount-scheme/if-you-live-in-scotland)):

- **Core group, automatic.** Under Schedule 1 to the Regulations:
  anyone on Pension Credit; Universal Credit claimants with the disabled
  child addition, or who are not in work and have a child under 5 or
  limited capability for work (with or without work-related activity);
  income-related ESA claimants with a child under 5, a pensioner, severe
  disability or enhanced disability premium, or limited capability for
  work or work-related activity; Income Support or income-based JSA
  claimants with a child under 5 or a pensioner, higher pensioner,
  disability, severe disability, enhanced disability or disabled child
  premium; and people receiving loans for mortgage interest through
  Pension Credit, or through one of those legacy benefits with a child
  under 5 or a qualifying premium. GOV.UK's summary is narrower.
- **Broader group, by application** to the energy supplier, which can
  set its own extra criteria.

The qualifying date is also 23 August 2026.

### Northern Ireland

The scheme doesn't operate in Northern Ireland: its primary legislation
extends to Great Britain only.

## Proposed scope

### Phase 1: England and Wales

Now a rule on benefit receipt:

- Parameter `gov.ofgem.warm_home_discount.amount`: £150, the
  "prescribed rebate" in both sets of 2026 Regulations (£150 since
  winter 2022-23; under the Warm Home Discount Regulations 2011 it was
  £140 from 2014-15 to 2021-22, after £120, £130 and £135 in the first
  three scheme years).
- Parameter listing the qualifying benefits by scheme year, since the
  2025-26 and 2026-27 lists differ, so a reform can widen or narrow the
  list.
- Variable `warm_home_discount` (Household, YEAR): the amount if the
  household is in England or Wales and any benefit unit receives a
  qualifying benefit. Read receipt from the modelled benefits, for
  example `universal_credit`, `housing_benefit`, `esa_income` and
  `pension_credit`, so that take-up carries through (`esa_income` is
  reported receipt, screened by capital and work tests).
- No separate take-up flag, since most rebates are paid through data
  matching without a claim (a minority must phone the helpline).

### Phase 2: Scotland core group

The core group can be built from the same benefit variables plus
Universal Credit's disabled child and limited capability for work
assessments, whether the claimant is in work, whether there is a child
under 5, and legacy-benefit premiums. ESA's pensioner premium and loans
for mortgage interest have no variables yet.

### Phase 3: Scotland broader group

Application-based, so it needs a take-up rate calibrated to Ofgem's
published recipient numbers for Scotland, on top of the eligible group.

## Data and calibration

- Ofgem's [Warm Home Discount reports and data](https://www.ofgem.gov.uk/environmental-and-social-schemes/warm-home-discount-whd/warm-home-discount-whd-reports-and-data)
  and annual reports: recipients and spend by group and country.
- DWP benefit caseloads, already used to calibrate the qualifying
  benefits.
- The 2025-26 impact assessment and government response give the
  expected number of recipients after the expansion. Use them to check
  Phase 1's aggregate.

## Open questions

- **Timing.** The scheme year runs from April to March, but rebates are
  paid in the winter: letters go out from late October and suppliers
  apply the discount by 31 March, with the qualifying date in August. A
  model year (6 April to 5 April) contains one scheme year's rebate, so
  pay it in the model year that contains the winter.
- **Who counts as the household.** The rebate attaches to an
  electricity account. In multi-benefit-unit households, decide whether
  one qualifying benefit unit is enough (simplest, and likely right for
  most households) and say so.
- **Electricity VAT interaction.** The rebate reduces the bill. If the
  model ever nets it off energy spending, it would interact with the
  domestic electricity VAT work in
  [#2189](https://github.com/PolicyEngine/policyengine-uk/pull/2189).
  Modelled as a benefit, it doesn't.

## References

- [The Warm Home Discount (England and Wales) Regulations 2026 (SI 2026/389)](https://www.legislation.gov.uk/uksi/2026/389/contents).
- [The Warm Home Discount (England and Wales) Regulations 2022 (SI 2022/772)](https://www.legislation.gov.uk/uksi/2022/772/contents).
- [The Warm Home Discount (Scotland) Regulations 2026 (SI 2026/488)](https://www.legislation.gov.uk/uksi/2026/488/contents).
- [The Warm Home Discount (Scotland) Regulations 2022 (SI 2022/1073)](https://www.legislation.gov.uk/uksi/2022/1073/contents).
- DESNZ, [Expanding the Warm Home Discount scheme, 2025 to 2026: government response](https://assets.publishing.service.gov.uk/media/6852e6e9679778c74ec15e82/expanding-the-warm-home-discount-scheme-2025-to-2026-government-response.pdf) and [impact assessment](https://assets.publishing.service.gov.uk/media/68529908ff16d05c5e6aa678/expanding-the-warm-home-discount-scheme-2025-to-2026-impact-assessment.pdf).
- DESNZ, [Warm Home Discount eligibility statement, England and Wales, 2025 to 2026](https://www.gov.uk/government/publications/warm-home-discount-eligibility-statement-england-and-wales-2025-to-2026-scheme-year/warm-home-discount-eligibility-statement-england-and-wales-2025-to-2026).
- [The Warm Home Discount Regulations 2011 (SI 2011/1033)](https://www.legislation.gov.uk/uksi/2011/1033/regulation/2): earlier rebate amounts.
- GOV.UK, [Warm Home Discount Scheme](https://www.gov.uk/the-warm-home-discount-scheme).
- Ofgem, [Warm Home Discount scheme pages](https://www.ofgem.gov.uk/environmental-and-social-schemes/warm-home-discount-whd) and [reports and data](https://www.ofgem.gov.uk/environmental-and-social-schemes/warm-home-discount-whd/warm-home-discount-whd-reports-and-data).
- Issue: [#502](https://github.com/PolicyEngine/policyengine-uk/issues/502).
