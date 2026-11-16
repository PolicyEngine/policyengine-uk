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

The couple jointly elect which of them has the entitlement; the Secretary of
State decides only where they don't. The data don't record the election, so
the model takes the one that gives the larger award: of the otherwise eligible
partners, the one whose candidate award is larger has the entitlement. The
model's own awards differ only under the Budget 2026 Carer's Allowance
earnings taper; everywhere else each eligible partner has the same rate. An
award that an input supplies can differ in any year, and the election then
follows it. Where the awards are equal, the model prefers a reported
recipient, then an eligible benefit-unit head, then the eldest eligible
partner, and member order breaks an age tie. That order is a modelling
convention, not statutory priority. An ineligible reported recipient or head
cannot displace an eligible partner. The caring-hours, earnings, age and
take-up conditions stay as they are.

In 2030-31, the year the taper starts, the model applies the election
separately to the weeks before the taper and the weeks under it, since the law
restricts entitlement day by day. Where the two partners have the same award
for those weeks, the couple elect the one with the larger award over the year,
and then the order above applies. A partner below the earnings limit has the
full rate in both parts and the larger award over the year, so the couple
elect them for the whole year, even where the other partner's award under the
taper equals the full rate, as it does at a taper rate of zero. Where both
partners earn over the limit, neither has an award before the taper, and the
couple elect the one with the larger award under it. Either way one partner
has the award for the year, at any taper rate of zero or more. A
`carers_allowance_pre_couple_limit` that an input supplies carries no dates,
so the restriction keeps one partner's award for the whole year.
The parts of the year reach the payment as shares of the year:
`carers_allowance_pre_overlap` is the amount from
`carers_allowance_pre_couple_limit` that the restriction keeps, and
overlapping benefits come off for the share of the year in which the
restriction keeps it.

The shares describe an amount only where the model's own formulas calculate
it from the parts of the year and, for every member of the benefit unit, it
is the amount the parts give: within half a penny, and an award, however
small, exactly where the parts give one, since the couple restriction chooses
only among partners with an award. An amount that an input supplies, or that
a reform neutralizes or calculates with a formula of its own, carries no
dates, even where it equals the model's: a value cannot show where it came
from. So does an amount that a reform changes while keeping the formula, for
example by adding `defined_for`. A `carers_allowance_pre_couple_limit` of that
kind gets the couple restriction for the whole year, and the whole year's
overlapping benefits come off what the restriction keeps. A
`carers_allowance_pre_overlap` of that kind comes after the couple
restriction, so only the whole year's overlapping benefits come off it.
Either way, the payment starts from that value, and where the
`carers_allowance_pre_overlap` is of that kind, the payment doesn't read the
stage before it. A reform that changes only a variable's label, say, keeps
the parts of the year. The test of the formula covers the whole variable, so
a reform that wraps the formula to change one person's amount moves every
amount to the whole-year treatment. The model treats less than half a penny
for the year, which in practice is floating-point residue where an
overlapping benefit equals the award, as nil, and pays a penny.

The election compares awards before overlapping benefits, so it doesn't always
maximise what the couple receive: it can choose a partner whose overlapping
benefits reduce CA or CSP to zero, where choosing the other partner would pay
something.

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
