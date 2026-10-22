# Benefit minimum ages

Computed Carer's Allowance, Carer Support Payment (CSP) and Disability Living
Allowance (DLA) mobility awards apply these minimum ages to each person's existing
annual `age` input:

| Computed benefit | Minimum age |
| --- | ---: |
| Carer's Allowance | 16 |
| CSP | 16 |
| Higher DLA mobility component | 3 |
| Lower DLA mobility component | 5 |

The Carer's Allowance condition appears in section 70(3) of the
[Great Britain Act](https://www.legislation.gov.uk/ukpga/1992/4/section/70) and its
[Northern Ireland counterpart](https://www.legislation.gov.uk/ukpga/1992/7/section/70).
CSP's condition is in
[regulation 4(1)](https://www.legislation.gov.uk/ssi/2023/302/regulation/4).
The DLA mobility ages and corresponding higher/lower routes appear in sections
73(1), (1A) and (11) of the
[Great Britain Act](https://www.legislation.gov.uk/ukpga/1992/4/section/73) and
[Northern Ireland Act](https://www.legislation.gov.uk/ukpga/1992/7/section/73).
Other qualifying conditions remain necessary. These gates do not implement a full
eligibility assessment or change education, caring, disability, duration, upper-age
or programme-replacement rules.

## Reported inputs and amount overrides

A positive `carers_allowance_reported` value or sufficient caring hours cannot
bypass the age condition in the computed CA/CSP pre-overlap amount. A DLA mobility
category similarly cannot bypass its category's age condition. The raw reported
amounts and categories remain stored inputs.

Explicitly supplying a pre-overlap or final amount keeps the model's generic input
override behavior. For example, an explicit `carers_allowance` or `dla_m` amount
can override its formula. Such an override is not evidence of statutory
entitlement. Report-only positive carer cases also preserve an existing proxy;
reported receipt does not legally waive the qualifying-care requirements.

DLA care has no categorical minimum-age floor. Its separate needs, duration and
child-comparison conditions still apply, as set out in
[section 72](https://www.legislation.gov.uk/ukpga/1992/4/section/72) and its
[Northern Ireland counterpart](https://www.legislation.gov.uk/ukpga/1992/7/section/72).
A care category for an infant assumes those conditions; it is not automatic
entitlement. DLA totals continue to add the care and mobility components.

## Dates and the annual model

The CA age parameter begins on 1 January 2015 as the model's existing coverage
anchor. This is not a claim that the legal age condition commenced in 2015.
CSP's raw age parameter starts on 19 November 2023, the commencement of regulation
4. The DLA mobility parameters start on 9 April 2001, as recorded in the Acts'
amendment annotations. These dates do not fill missing historical benefit rates
or expand the existing Scottish CA-to-CSP model switch from 2025.

`age` is a Person/YEAR floating-point stock, with an existing default of 40 when
omitted. The gates compare it directly, without flooring or rounding fractional
ages. Awards retain the existing annual rate-times-52 convention. They do not
calculate exact birthdays, part-year awards or award weeks. In particular, this
does not newly implement CSP regulation 4(2)'s leap-day birthday rule.

At the unchanged 2026 rates, an otherwise qualifying carer aged 16 receives
£4,495.40 before overlap; an under-16 computed award is zero. Higher and lower DLA
mobility amounts are respectively £4,160 and £1,575.60 annually once the relevant
age floor is met. These conditional examples do not estimate a population effect
or establish independently encoded parity.

## Combined CSP conditions

This change is stacked on the repaired [PR #2473](https://github.com/PolicyEngine/policyengine-uk/pull/2473).
Both the age condition and the earnings condition apply to computed CSP, including
the reported-Carer’s-Allowance input proxy. Natural-pay cases combine age15,
fractional ages below16, age16, the exact annual earnings limit and favorable
fractional-penny treatment. The shared reader retains merged [PR #2444](https://github.com/PolicyEngine/policyengine-uk/pull/2444)
NI-age deductions. Existing annual/award-week, PAYE and care-charge qualifications
remain in the [CSP earnings assumptions](carer-support-payment-earnings.md).

Only after #2473 actually merges should this branch be retargeted and revalidated
on current main; a queue entry or passing checks do not establish that landing.
The shared-parameter change in open [PR #2518](https://github.com/PolicyEngine/policyengine-uk/pull/2518)
requires future CSP-reader/prose coordination; it is not copied or repaired here.
