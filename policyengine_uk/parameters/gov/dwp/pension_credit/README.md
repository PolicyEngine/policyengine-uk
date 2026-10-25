# Pension Credit

After the last published rates, the standard minimum guarantee rises each
April with the previous May-July total-pay average weekly earnings increase,
using the same statutory input and published precision as the State Pension
triple lock. This models the earnings minimum in
[SSAA 1992 s150A(2)](https://www.legislation.gov.uk/ukpga/1992/5/section/150A),
with no decrease when earnings fall. There is no CPI or 2.5% floor in this
projection. The shared index is
`gov.economic_assumptions.indices.earnings_uprating`. The three lower Housing
Benefit pension-age personal allowances (`aged_from_cutoff`), for those who
reached the qualifying age on or after 1 April 2021, follow the same increase.

The Savings Credit maximum rises with September CPI, following
[HCWS1101](https://questions-statements.parliament.uk/written-statements/detail/2025-11-26/hcws1101).
The maximum has a non-negative CPI floor. Unreformed projected thresholds are
derived from the component indices before general uprating:
`threshold = max(0, standard minimum guarantee - maximum / phase_in)`.
At the 60% phase-in rate, this ensures that the formula's maximum award
follows prices even when the guarantee follows earnings. Published
thresholds are retained, including their rounding. If the enacted phase-in
rate is zero, the projection retains the previous threshold rather than
dividing by zero.

The three higher Housing Benefit pension-age personal allowances, for those
who reached the qualifying age before 1 April 2021, are based on the guarantee
plus maximum Savings Credit
([DWP HB A3/2021, paragraphs 3–5](https://www.gov.uk/government/publications/housing-benefit-adjudication-circulars-2021/a32021-housing-benefit-person-who-have-attained-the-qualifying-age-for-state-pension-credit-amendment-regulations-2021)).
Published allowances are retained exactly, including their rounding. In the
unreformed forecast, each higher allowance equals the projected guarantee plus
the projected maximum, so its guarantee part follows earnings and its maximum
part follows September CPI.

## Projection base and reforms

The projection base is the last year with explicit enacted values for both
guarantees, both Savings Credit thresholds and the three higher Housing
Benefit allowances. All seven parameters must reach the same year. If they
do not, parameter loading raises an error listing each parameter and its last
enacted year. Reform dates do not move this base.

A reform to the Pension Credit guarantee or Savings Credit phase-in rate does
not re-derive the separately set Savings Credit threshold or Housing Benefit
allowances. Explicit threshold and allowance reforms remain anchors for their
own later projections. Each higher allowance has its own index, including the
lone-parent allowance. A base-year allowance at or below its guarantee follows
earnings, so reducing an allowance below the guarantee or setting it to zero
does not prevent the tree building. Projected thresholds and higher allowances
are floored at zero.

These rules describe forecasts after the enacted rates, rather than announced
future benefit amounts. The public [Pension Credit documentation](https://policyengine.github.io/policyengine-uk/programs/gov/dwp/pension-credit.html#uprating)
summarises them alongside the programme's eligibility and rate information.
