# Pension Credit

After the last published rates, the standard minimum guarantee rises each
April with the previous May-July total-pay average weekly earnings increase,
using the same statutory input and published precision as the State Pension
triple lock. This models the earnings minimum in
[SSAA 1992 s150A(2)](https://www.legislation.gov.uk/ukpga/1992/5/section/150A),
with no decrease when earnings fall. There is no CPI or 2.5% floor in this
projection. The six Housing Benefit pension-age personal allowances follow
the same increase.

The Savings Credit maximum rises with September CPI, following
[HCWS1101](https://questions-statements.parliament.uk/written-statements/detail/2025-11-26/hcws1101).
Projected thresholds are derived after uprating:
`threshold = standard minimum guarantee - maximum / phase_in`.
At the 60% phase-in rate, this ensures that the formula's maximum award
follows prices even when the guarantee follows earnings. Published
thresholds are retained, including their rounding.
