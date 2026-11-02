from policyengine_uk.model_api import *


class salary_sacrifice_pension_ni_excess(Variable):
    label = "Salary sacrifice pension contributions subject to NICs"
    documentation = (
        "Employer pension contributions through salary sacrifice above the NICs "
        "exemption cap. This is added only to Class 1 earnings: it is neither "
        "cash employment income nor an actual member pension contribution. "
        "The existing annual model samples the 2029-04-06 cap; payroll interval "
        "rules and individual transaction dates are not modelled."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2026/15/section/1/enacted"

    def formula(person, period, parameters):
        sacrifice = person(
            "pension_contributions_via_salary_sacrifice_from_pay", period
        )
        cap = parameters(
            period
        ).gov.hmrc.national_insurance.salary_sacrifice_pension_cap
        return max_(sacrifice - cap, 0)
