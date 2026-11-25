from policyengine_uk.model_api import *


class payroll_giving(Variable):
    value_type = float
    entity = Person
    label = "Payroll Giving donations from employment pay"
    documentation = (
        "Actual qualifying donations withheld from employment pay, including "
        "employer-paid statutory sick, maternity and paternity pay, under an "
        "approved Payroll Giving scheme and allowed as a deduction under "
        "Part 12 of ITEPA. Supply the non-negative, legally allowed amount "
        "for the relevant employment and tax year, not a requested gift or "
        "an amount exceeding the pay from which it was withheld. Employment "
        "income must be gross of these donations. Household income measures do "
        "not subtract the donation as voluntary spending; tax and benefit "
        "effects flow through those measures. This input excludes "
        "donations withheld from pensions or other social security benefits, "
        "or from exempt or non-PAYE income. Do not also include the same "
        "donation in Gift Aid "
        "or employment expenses. Allowable employment expenses must respect "
        "the earnings remaining after Payroll Giving and other deductions "
        "outside Part 5 of ITEPA. The model does not determine scheme "
        "approval, donation eligibility or per-employment limits from raw "
        "requested amounts."
    )
    definition_period = YEAR
    quantity_type = FLOW
    unit = GBP
    reference = (
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 713(1)-(5)",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/713",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 329(3)",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/329",
        ),
    )
