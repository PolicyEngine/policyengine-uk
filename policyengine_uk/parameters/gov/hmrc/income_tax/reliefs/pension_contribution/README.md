# Pension contributions

Relevant UK earnings for pension contribution relief include employer-paid,
taxable statutory sick pay and statutory maternity pay. The model holds these
payments in `employment_benefits`, separately from `employment_income`, and
includes that aggregate once when limiting relief. Pension income does not
increase the relevant-earnings limit. The existing age limit, relief-at-source
basic amount and nonnegative trading-profit rules still apply.

This follows [Finance Act 2004 section 189](https://www.legislation.gov.uk/ukpga/2004/12/section/189)
and [HMRC PTM044100](https://www.gov.uk/hmrc-internal-manuals/pensions-tax-manual/ptm044100).
The annual monetary inputs represent actual employer-paid taxable payments;
they do not establish statutory-pay eligibility or identify exceptional payments
made directly by HMRC in survey data.

Statutory paternity pay still depends on the separate change in
[PR #2368](https://github.com/PolicyEngine/policyengine-uk/pull/2368) to include it
in the taxable employment aggregate. This change addresses the existing SSP/SMP
omission in issue #2371; it does not complete that issue's SPP dependency.
