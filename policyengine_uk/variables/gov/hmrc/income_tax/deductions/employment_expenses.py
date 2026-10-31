from policyengine_uk.model_api import *


class employment_expenses(Variable):
    value_type = float
    entity = Person
    label = "Allowable employment expenses"
    documentation = (
        "Employment expenses allowed as a deduction under Chapter 2 of Part 5 "
        "of ITEPA, after the applicable relevant-employment and other deduction "
        "limits. Supply the legally allowed amount, not all raw work costs. "
        "Amounts paid on the employee's behalf, and reimbursements, qualify "
        "only to the extent required by sections 333 and 334, including their "
        "inclusion in earnings. Do not deduct the same costs twice. The model "
        "does not determine admissibility or per-employment limits from this "
        "person-level total."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 ss. 333 and 334",
            href="https://www.legislation.gov.uk/ukpga/2003/1/part/5/chapter/2",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 ss. 328 to 330",
            href="https://www.legislation.gov.uk/ukpga/2003/1/part/5/chapter/1",
        ),
    ]
    unit = GBP
