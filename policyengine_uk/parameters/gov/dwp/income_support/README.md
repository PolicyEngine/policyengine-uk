# Income Support

The means test includes the claimant's and partner's gross statutory sick,
maternity and paternity pay through the separate `statutory_sick_pay`,
`statutory_maternity_pay` and `statutory_paternity_pay` inputs. These payments
count as other income: [regulation 35(2)(b)](https://www.legislation.gov.uk/uksi/1987/1967/regulation/35)
excludes employer illness and statutory leave pay from earnings, while
[regulation 40(4)(a)](https://www.legislation.gov.uk/uksi/1987/1967/regulation/40)
includes it in income other than earnings. [Schedule 9, paragraphs 1 and 4](https://www.legislation.gov.uk/uksi/1987/1967/schedule/9)
provides for deductions for relevant income tax, primary Class 1 National
Insurance and half of qualifying pension contributions.

The model currently deducts annual income tax, National Insurance and pension
contributions without attributing them to particular payments. It also applies
one claimant-type earnings disregard to combined income. As a result, a case
with statutory pay but unused earnings disregard can have understated assessable
income. Including gross statutory pay does not resolve these existing deduction
and disregard limitations.

The activation parameter turns off on 1 April 2026. The full-year 2027 award is
zero.
