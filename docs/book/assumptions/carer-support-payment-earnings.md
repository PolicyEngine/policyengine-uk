# Carer Support Payment earnings

Carer Support Payment (CSP) has an earnings limit. Regulation 14 of the
[Carer's Assistance Regulations 2023](https://www.legislation.gov.uk/ssi/2023/302/regulation/14)
excludes a carer when the earnings counted for the relevant award week exceed
the limit. A reported Carer's Allowance award does not exempt them.

## Limits and penny fractions

CSP has its own Sunday effective dates, separate from Carer's Allowance:

| Effective date | Weekly limit |
| --- | ---: |
| 19 November 2023 | £139 |
| 7 April 2024 | £151 |
| 6 April 2025 | £196 |
| 5 April 2026 | £204 |

The limit is inclusive. [Schedule 2 paragraph 4](https://www.legislation.gov.uk/ssi/2023/302/schedule/2/paragraph/4)
handles a fractional penny in the individual's favour. At the final earnings
test, £204.005 a week counts as £204.00 and passes; £204.01 exceeds the £204
limit. The model compares annual earnings with the first excluded weekly
penny amount multiplied by 52, in the earnings array's numeric precision.
This applies the penny rule without an extra tolerance or rounding annual
earnings before converting them to a weekly amount.

## Annual earnings approximation

The model reuses `carers_allowance_earnings`, a Person-level annual amount in
pounds. It deducts modelled employment tax and primary Class 1 contributions,
notional tax and contributions on self-employment profits, and half the
individual's pension contributions. Partner and cared-for-person earnings do
not enter the carer's test. Employer pension contributions are not deducted.

Annual net earnings are spread evenly over 52 weeks. Constant-through-year
inputs match the weekly comparison; varying earnings may not. Originally,
regulation 14 assessed that award week's earnings. From 16 November 2025 it
assesses the immediately preceding award week. Annual inputs cannot distinguish
those weeks or reproduce all pay-period and averaging cases in schedule 2.

The shared reader approximates employment tax using PAYE on pay alone with a
standard code, rather than actual withholding. It does not represent all
statutory care-charge deductions and disregards. Reusing it does not certify
that every schedule 2 calculation is implemented.

## Coverage and other conditions

Raw parameter dates retain the statutory dates above. The existing annual
parameter conversion samples 30 April for a named fiscal year; the model's
2026 value therefore represents the £204 limit, rather than a claim that it
legally began on 1 January. CSP remains modelled from 2025, with the previous
Carer's Allowance route retained for Scotland in earlier model years. This
change does not extend coverage back to the 2023 pilot.

The existing caring-hours, reported-receipt and take-up conditions remain.
Age, education, the cared-for person's qualifying-benefit conditions and the
full claim-status rules are separate gaps. Earnings above the limit remove
underlying CSP entitlement before the overlapping-benefit calculation. This
differs from an overlapping benefit reducing an otherwise entitled person's
payment to zero. The Scottish Carer Supplement is paid only when CSP is
payable. Caring hours and reported caring can still qualify a person for the
Universal Credit carer element, which does not apply this earnings limit.

## Integration dependencies

The shared Carer’s Allowance earnings reader retains the age-conditioned Class 2
and Class 4 deductions from merged [PR #2444](https://github.com/PolicyEngine/policyengine-uk/pull/2444).
Natural trading-income cases cover exemption after State Pension age and Class 4
liability in the tax year that pensionable age is reached. The existing annual
approximation remains. [PR #2474](https://github.com/PolicyEngine/policyengine-uk/pull/2474)
is the separate minimum-age change and must retain this earnings condition when
stacked or integrated.

The open [PR #2518](https://github.com/PolicyEngine/policyengine-uk/pull/2518)
changes a shared Carer’s Allowance earnings parameter. Once this reader is shared
with CSP, that parameter’s effects on CSP require coordination and validation;
this page does not assume the two benefits remain independent of that parameter.

## Couples caring for the same person

[SSCBA 1992 section 70(7ZA)](https://www.legislation.gov.uk/ukpga/1992/4/section/70),
the [Northern Ireland counterpart, section 70(7ZA)](https://www.legislation.gov.uk/ukpga/1992/7/section/70),
and [CSP regulation 5(3)](https://www.legislation.gov.uk/ssi/2023/302/regulation/5)
restrict multiple relevant entitlements for the same cared-for person. The
model applies the allowance restriction to the claimant and partner when
`partners_care_for_same_severely_disabled_person` is true. It removes the
second candidate entitlement before reducing either payment for overlapping
benefits. A selected carer whose overlapping benefit removes the payment
still retains the underlying entitlement.

The law provides election or decision rules; the model does not observe that
choice. Among otherwise eligible partners, it prefers a reported recipient,
then an eligible benefit-unit head, then the eldest eligible partner. Member
order breaks an age tie. This is a modelling convention, not statutory
priority. An ineligible reported recipient or head cannot displace an eligible
partner. The caring-hours, earnings, age and take-up conditions are unchanged.

The existing same-person default remains: two qualifying reported awards, or
awards that caring hours and take-up cannot explain, indicate different care
targets. Directly supplied payment, pre-overlap or entitlement inputs remain
authoritative. The default reads candidate amounts and supplied inputs before
the couple restriction, so it does not depend on the final awards it limits.
A cached calculation is not treated as a supplied award. Where relationships
are known, supply the same-person flag and claimant/partner flags explicitly.

This restriction covers units with exactly two claimant/partner flags. It
does not identify care targets across benefit units, allocate awards to other
members, or settle malformed units with more than two partners. The model
still uses caring hours or reported receipt as a proxy for the cared-for
person's qualifying conditions. The statutory coordination with another
person's UC carer element is a separate limitation: the existing UC allocation
can choose a different person from the allowance convention. The couple fix
does not certify that cross-programme allocation. Scottish Carer Supplement
remains separate from the CSP component and follows CSP actually payable.
