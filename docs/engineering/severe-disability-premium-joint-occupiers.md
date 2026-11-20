# Severe disability premium joint occupier input

`severe_disability_premium_joint_occupier_exclusion_applies` is a yearly
benefit-unit boolean input with a default of `false`. It supplies a statutory
assertion for the shared legacy severe disability premium non-dependant test.
Existing datasets and household inputs retain their previous treatment unless
they explicitly supply this new fact.

For a benefit unit to supply `true`, every other modelled rent-liable claimant
or partner must meet the applicable joint-occupier or separate-landlord-liability
exclusion relative to that benefit unit and year, for every applicable programme
using the shared test. The assertion covers every person selected by
`is_liable_for_household_rent`, including both partners where the model treats
both as liable. Each benefit unit supplies its own assertion for the relevant
year; another family's assertion is never inherited.

The legal conditions differ. Housing Benefit regulations 3(2)(d) and 3(3)
include the regulation 9(1) treated-as-not-liable exception. Income Support
regulations 3(2B) and 3(2C) include the close-relative and liability-acquisition/
first-occupation history conditions. Regulation 3(4) addresses separately
landlord-liable occupiers. The input requires the caller to establish the
applicable conditions; the model does not derive them from rent, age, family
roles or `liable_for_share_of_household_rent`.

Leave the input `false` when facts are unknown, any selected person fails the
conditions, or only a subset is known to qualify. A single boolean cannot
represent a mixed eligible and ineligible subset. `false` means the full
assertion is unestablished, rather than establishing that anyone is a
non-dependant.

The assertion affects the gate only when the target benefit unit itself has a
claimant or partner selected by `is_liable_for_household_rent`. The gate removes
other countable liable claimants and partners consistently from the household
count and the own-family subtraction. An adult non-family member of the same
benefit unit and a non-paying third adult remain countable unless an existing
independent exemption applies. Qualifying-benefit, blindness, age, own-family
and carer conditions retain their existing definitions.

This bounded interface addresses [issue #2181](https://github.com/PolicyEngine/policyengine-uk/issues/2181).
Primitive relationship, personal liability and history facts, automatic
inference and mixed-subset treatment remain unmodelled. Co-ownership,
commercial landlord/lodger and engaged charity-carer facts are not inferred.
The independent Scottish working-age CTR, CTR head-applies-alone, Pension Credit,
bedroom and non-dependant deduction predicates remain unchanged. The three
references below do not certify every downstream CTR or DfE regime or Northern
Ireland legal coverage. No full issue closure, national accuracy, rate or
verified-year coverage claim follows from this input.

## References

- [Housing Benefit Regulations 2006, regulation 3](https://www.legislation.gov.uk/uksi/2006/213/regulation/3).
- [Housing Benefit (Persons who have attained the qualifying age for state pension credit) Regulations 2006, regulation 3](https://www.legislation.gov.uk/uksi/2006/214/regulation/3).
- [Income Support (General) Regulations 1987, regulation 3](https://www.legislation.gov.uk/uksi/1987/1967/regulation/3).
