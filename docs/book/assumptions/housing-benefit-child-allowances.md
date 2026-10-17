# Housing Benefit child personal allowances

PolicyEngine does not currently calculate ordinary child personal allowances in
the Housing Benefit applicable amount. This omission applies before, during and
after the historical two-child restriction. The model calculates an adult
personal allowance from the benefit unit's composition and age, then adds the
premiums selected by `benefits_premiums`. It does not calculate an ordinary
allowance for either the first two children or additional children. See
`housing_benefit_applicable_amount` in
[`policyengine_uk/variables/gov/dwp/housing_benefit/`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/variables/gov/dwp/housing_benefit/housing_benefit_applicable_amount.py).

The historical rules below explain the omitted component and the information a
future implementation would need. They do not describe a calculation currently
supported by the model. Historical cash rates and household or population
impacts are outside this page's scope.

## The historical restriction

Before the restriction, each qualifying child or young person could contribute
a personal allowance to the applicable amount, the income threshold used in the
Housing Benefit means test. The later default restriction limited these
allowances to two, subject to transitional protection and the Child Tax Credit
assessment described below. It applied to ordinary child personal allowances;
bedroom entitlement and child disability premiums remained separate. See
[DWP Circular A5/2017, paragraphs 2–13](https://assets.publishing.service.gov.uk/media/5a820708ed915d74e6235650/a5-2017.pdf).

The legal dates differ by jurisdiction and age regime:

| Change | Great Britain | Northern Ireland |
| --- | --- | --- |
| Default restriction began | 6 April 2017 | 11 May 2017 |
| Restriction ended for pension-age Housing Benefit | 8 June 2024 | 8 June 2024 |
| Restriction ended for working-age Housing Benefit | 6 April 2026 | 6 April 2026 |

The commencement provisions are [SI 2017/376, regulation 1](https://www.legislation.gov.uk/uksi/2017/376/regulation/1/made)
and [SR 2017/79, regulation 1(2)](https://www.legislation.gov.uk/nisr/2017/79/regulation/1/made).
The pension-age amendments are [SI 2024/611, regulations 1 and 6](https://www.legislation.gov.uk/uksi/2024/611/made)
and [SR 2024/119, regulations 1 and 5](https://www.legislation.gov.uk/nisr/2024/119/made).
The working-age amendments are [SI 2026/316, regulations 1, 2 and 4](https://www.legislation.gov.uk/uksi/2026/316/made)
and [SR 2026/68, regulations 1, 2 and 4](https://www.legislation.gov.uk/nisr/2026/68/made).
These are legal commencement dates. An annual model period or annual parameter
sampling convention does not change them. Removing the count restriction did
not remove the other conditions for Housing Benefit or a child allowance.

## Protection attached to individual children

Transitional protection applied where the claimant was entitled to Housing
Benefit and the claimant or partner was responsible for more than two children
or young people in the household on 5 April 2017 in Great Britain, or 10 May
2017 in Northern Ireland. The protection attached to those individuals. Making
a new Housing Benefit claim ended that protection.

Becoming responsible for a new child brought the amended rules into play, while
allowances for the original protected individuals continued under the
transitional provisions. Those individuals also occupied spaces under the
default two-child rule when considering an allowance for a new child. For
example, three protected children remaining in the household plus a new baby
could retain three allowances, assuming no new claim and no more favourable
Child Tax Credit assessment. The new baby did not automatically reduce the
count to two or increase it to four. See [SI 2017/376, regulation 9](https://www.legislation.gov.uk/uksi/2017/376/regulation/9/made),
[SR 2017/79, regulation 8](https://www.legislation.gov.uk/nisr/2017/79/regulation/8/made)
and DWP Circular A5/2017, paragraphs 15–16 and example 3.

## The Child Tax Credit assessment mattered

Housing Benefit could use the children for whom the ordinary individual Child
Tax Credit element was included in the maximum-rate assessment, where that
produced a higher child-allowance amount. This comparison also preserved the
transitional protected amount as the alternative. The rule applied whether or
not Child Tax Credit was payable. A properly made, fully assessed nil-payment
award could therefore establish that more than two children were included;
an unexplained zero payment could not establish it. See [Housing Benefit
regulation 22(3)–(5), as at 1 April 2025](https://www.legislation.gov.uk/uksi/2006/213/regulation/22/2025-04-01),
[SR 2017/79, regulation 6](https://www.legislation.gov.uk/nisr/2017/79/regulation/6/made)
and DWP Circular A5/2017, paragraphs 9–14 and Annex A.

Historical Child Tax Credit rules retained ordinary child elements for children
born before 6 April 2017 and allowed conditional exceptions for later children,
including multiple births, adoption, non-parental care and non-consensual
conception. The adoption and non-parental-care treatment changed on 28 November
2018. These exceptions required their own conditions and assessment; generic
household flags do not establish them. For example, two existing children plus
twins could give three ordinary child elements where the actual assessment
included one additional twin. Four elements did not follow automatically from
the multiple birth. [HMRC's historical exceptions guidance](https://www.gov.uk/guidance/child-tax-credit-exceptions-to-the-2-child-limit)
sets out the conditions and the 2018 change.

A positive Child Tax Credit payment also cannot identify the ordinary-child
count. Disability and childcare elements could be included for a child without
an ordinary individual child element. The required information is which
children the ordinary-element assessment included, rather than whether any
Child Tax Credit cash was paid. These historical assessment rules do not imply
that new Child Tax Credit claims remain available today.

## Implementation remains deferred

Current ages and family size do not establish which individual children were
protected, whether a later new Housing Benefit claim ended protection, or what
an ordinary-child-element assessment included. A payment amount alone cannot
fill those gaps, and sensitive exception assessments must not be reconstructed
from generic household characteristics.

[Issue #2232](https://github.com/PolicyEngine/policyengine-uk/issues/2232)
keeps implementation of this component, labelled C1 in the update plan,
deferred. This includes the proposal to implement only unrestricted periods.
A future design needs agreement on the required facts, their data sources,
behaviour when facts are absent, and changes within a year. A pre-assessed
included-child count is one possible interface for that discussion; it is not
a supported model input. This documentation introduces no claim-history or
exception inputs and changes no calculation.

Child disability premiums and the protected family premium are separate work
under [#2221](https://github.com/PolicyEngine/policyengine-uk/issues/2221) and
[#2223](https://github.com/PolicyEngine/policyengine-uk/issues/2223). This page
does not revive [closed PR #2198](https://github.com/PolicyEngine/policyengine-uk/pull/2198)
or its associated issues.
