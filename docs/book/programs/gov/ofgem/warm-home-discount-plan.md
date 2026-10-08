# Warm Home Discount (planned)

```{warning}
**Not yet modelled.** The Warm Home Discount (WHD) is a £150 rebate off
a household's electricity bill each winter, paid by energy suppliers
under schemes that Ofgem administers. PolicyEngine UK doesn't model it.
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

Under the 2022 Regulations, the means-tested group had to pass a
"high cost to heat" test based on property data. For winter 2025-26
that test was removed, so every household on a qualifying means-tested
benefit got the rebate: around 6 million households in Great Britain,
2.7 million more than the year before
([government response, June 2025](https://assets.publishing.service.gov.uk/media/6852e6e9679778c74ec15e82/expanding-the-warm-home-discount-scheme-2025-to-2026-government-response.pdf)).

For winter 2026-27, GOV.UK
([eligibility in England and Wales](https://www.gov.uk/the-warm-home-discount-scheme/if-you-live-in-england-and-wales))
says a household qualifies if, on the qualifying date of 23 August
2026, its electricity supplier is in the scheme and the person or
their partner gets one of:

- Universal Credit;
- Housing Benefit;
- income-related Employment and Support Allowance;
- Pension Credit.

The rebate is applied automatically.

### Scotland

The scheme runs under separate Scottish regulations
([2022](https://www.legislation.gov.uk/uksi/2022/1073/contents), SI
2022/1073; 2026 Regulations running to 31 March 2031 have been laid in
draft). For winter 2026-27
([eligibility in Scotland](https://www.gov.uk/the-warm-home-discount-scheme/if-you-live-in-scotland)):

- **Core group, automatic:** Pension Credit; Universal Credit with an
  extra amount for a disability or health condition; income-related ESA
  with a disability or pensioner premium; or a Support for Mortgage
  Interest loan with one of those premiums. Also people responsible for
  a child under 5 who are unemployed and on Universal Credit or
  income-related ESA, or have a Support for Mortgage Interest loan.
- **Broader group, by application** to the energy supplier, which can
  set its own extra criteria.

The qualifying date is also 23 August 2026.

### Northern Ireland

The scheme doesn't operate in Northern Ireland: its primary legislation
extends to Great Britain only.

## Proposed scope

### Phase 1: England and Wales

Now a rule on benefit receipt:

- Parameter `gov.ofgem.warm_home_discount.amount`: £150 (£140 before
  winter 2022-23). Check the 2026 Regulations for any change.
- Parameter listing the qualifying benefits, so a reform can widen or
  narrow the list.
- Variable `warm_home_discount` (Household, YEAR): the amount if the
  household is in England or Wales and any benefit unit receives a
  qualifying benefit. Read receipt from the modelled benefits, for
  example `universal_credit`, `housing_benefit`, `esa_income` and
  `pension_credit`, so that take-up carries through.
- No separate take-up flag, since the rebate is paid without a claim.

### Phase 2: Scotland core group

The core group can be built from the same benefit variables plus the
Universal Credit disability elements, the ESA premiums and the age of
the youngest child.

### Phase 3: Scotland broader group

Application-based, so it needs a take-up rate calibrated to Ofgem's
published recipient numbers for Scotland, on top of the eligible group.

## Data and calibration

- Ofgem's [Warm Home Discount pages](https://www.ofgem.gov.uk/environmental-and-social-schemes/warm-home-discount-whd):
  recipients and spend by group and country.
- DWP benefit caseloads, already used to calibrate the qualifying
  benefits.
- The 2025-26 impact assessment and government response give the
  expected number of recipients after the expansion. Use them to check
  Phase 1's aggregate.

## Open questions

- **Timing.** The scheme year runs from October to March, with the
  qualifying date in August. A model year (April to March) contains one
  winter's rebate, so pay the rebate in the year that contains the
  winter.
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
- [The Warm Home Discount (Scotland) Regulations 2022 (SI 2022/1073)](https://www.legislation.gov.uk/uksi/2022/1073/contents).
- DESNZ, [Expanding the Warm Home Discount scheme, 2025 to 2026: government response](https://assets.publishing.service.gov.uk/media/6852e6e9679778c74ec15e82/expanding-the-warm-home-discount-scheme-2025-to-2026-government-response.pdf).
- GOV.UK, [Warm Home Discount Scheme](https://www.gov.uk/the-warm-home-discount-scheme).
- Ofgem, [Warm Home Discount scheme pages and reports](https://www.ofgem.gov.uk/environmental-and-social-schemes/warm-home-discount-whd).
- Issue: [#502](https://github.com/PolicyEngine/policyengine-uk/issues/502).
