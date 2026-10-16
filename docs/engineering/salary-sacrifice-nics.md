# Salary sacrifice and the NICs cap

`employment_income` supplies cash pay after contractual salary sacrifice, and
`pension_contributions_via_salary_sacrifice` supplies the employer contribution
separately. UKSimulation preserves this existing input convention; the model
does not deduct that sacrifice a second time from cash pay.

The cap limits NIC exemption, rather than returning ordinary pay or creating a
member pension payment. `salary_sacrifice_pension_ni_excess` adds the excess once
to `ni_class_1_income`. Full actual sacrifice still counts once in the current
DC pension-input proxy. The capped `..._adjusted` measure is the NIC-exempt
amount. The two NI reporting measures remain approximations; actual liability
uses the Class 1 curves and age flags.

The legacy `salary_sacrifice_returned_to_income` defaults to zero. Explicit
ordinary-return inputs retain their previous pay/member-payment semantics.
Actual reported member payments and the separate broad-base haircut assumption
are unchanged. Age-75 member accounting and annual-allowance taper work in draft
#2441 remain separate; landing either change requires retaining that work.

The [NICs Act 2026](https://www.legislation.gov.uk/ukpga/2026/15/enacted)
provides the contributions-law machinery for 2029–30 onwards. The existing
2029-04-06 parameter and annual sampling are retained. This is not a complete
implementation of future payroll-interval regulations. Employer contributions
remain subject to [ITEPA 2003 s308](https://www.legislation.gov.uk/ukpga/2003/1/section/308);
member relief separately follows [FA 2004 ss188–191](https://www.legislation.gov.uk/ukpga/2004/12/section/188).
