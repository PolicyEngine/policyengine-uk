from policyengine_uk.model_api import *


class pension_contributions_for_annual_allowance(Variable):
    value_type = float
    entity = Person
    label = "Total pension contributions counting toward the Annual Allowance"
    documentation = (
        "The pension input amount for Annual Allowance purposes, including "
        "employee, personal, employer, and salary sacrifice contributions. "
        "Per Finance Act 2004 s.233, the pension input amount for money "
        "purchase arrangements includes both individual contributions and "
        "employer contributions."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Finance Act 2004 s. 233",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/233",
        ),
        dict(
            title="HMRC: Annual Allowance",
            href="https://www.gov.uk/tax-on-your-private-pension/annual-allowance",
        ),
    ]
    unit = GBP

    adds = [
        "employee_pension_contributions",
        "personal_pension_contributions",
        "employer_pension_contributions",
        "pension_contributions_via_salary_sacrifice_adjusted",
    ]
