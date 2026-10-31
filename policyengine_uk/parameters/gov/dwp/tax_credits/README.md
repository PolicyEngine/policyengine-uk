# Tax Credits

The model includes the child, family and disability elements in the Child Tax
Credit maximum only when `is_CTC_eligible` is true. [Sections 8 and 9 of the Tax
Credits Act 2002](https://www.legislation.gov.uk/ukpga/2002/21/section/8)
set the entitlement and maximum-rate framework; [section 9](https://www.legislation.gov.uk/ukpga/2002/21/section/9)
provides the elements of that maximum.

`would_claim_CTC` records whether the family would claim an eligible award. It
does not establish eligibility. The existing legacy-claim eligibility rule uses
reported Child Tax Credit and excludes Universal Credit claimants and families
whose legacy benefits have closed. A family that would claim but fails that
rule has no Child Tax Credit maximum to enter the tax credit income calculation.

`tax_credits` combines the pre-minimum Child Tax Credit and Working Tax Credit
awards and applies the shared minimum-payment rule. Housing Benefit and Council
Tax Reduction read this combined award as income. Gating each element prevents
an ineligible family's child element from reducing those benefits through tax
credit income that the family does not receive.
