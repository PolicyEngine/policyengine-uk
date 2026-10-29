# Income Support

The means test includes the claimant's and partner's gross statutory sick,
maternity and paternity pay through the separate `statutory_sick_pay`,
`statutory_maternity_pay` and `statutory_paternity_pay` inputs. These payments
count as other income: [regulation 35(2)(b)](https://www.legislation.gov.uk/uksi/1987/1967/regulation/35)
excludes remuneration for periods of illness and specified parental leave from
earnings, while [regulation 40(1)](https://www.legislation.gov.uk/uksi/1987/1967/regulation/40)
treats it as income other than earnings. [Schedule 9, paragraphs 1 and 4](https://www.legislation.gov.uk/uksi/1987/1967/schedule/9)
provides for deductions for relevant income tax, primary Class 1 National
Insurance and half of qualifying pension contributions.

The earnings disregard applies only to the claimant's and partner's combined
net earnings, calculated by `income_support_net_earnings`. The
`income_support_earnings_disregard` variable caps the selected weekly amount,
annualised over 52 weeks, at those annual net earnings: £20 for a lone parent,
£10 shared by a couple, or £5 for a single claimant. These baseline amounts come
from
[Schedule 8, paragraphs 5, 6(a) and 9](https://www.legislation.gov.uk/uksi/1987/1967/schedule/8);
[regulations 36(2)](https://www.legislation.gov.uk/uksi/1987/1967/regulation/36)
and [38(2)](https://www.legislation.gov.uk/uksi/1987/1967/regulation/38) apply them
to net earnings and profit. With £3,000 of statutory maternity pay and no
earnings, the disregard is zero and applicable income is £3,000. Unused earnings
disregard cannot reduce statutory pay, pensions, benefits or maintenance.

The model deducts annual income tax, National Insurance and half of pension
contributions once from combined income. To determine the earnings cap, it
separately approximates earnings' income tax using their share of raw income
and Class 1 contributions using the non-statutory share of the Class 1 base;
Class 2 and Class 4 contributions are deducted in full. These annual allocations
do not identify actual payroll deductions or calculate the separate notional
tax on self-employment required by the regulations. Pension contributions are
not split between earnings and sick/leave pay, and employer enhancements to
sick/leave pay are not separated from employment income. Additional Schedule 8
disability, carer, occupation and past-employment disregards remain unmodelled.

The activation parameter turns off on 1 April 2026. The full-year 2027 award is
zero.
