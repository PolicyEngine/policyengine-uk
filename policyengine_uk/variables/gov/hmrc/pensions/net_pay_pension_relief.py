from policyengine_uk.model_api import *


class net_pay_pension_relief(Variable):
    value_type = float
    entity = Person
    label = "Pension contributions relieved under a net pay arrangement"
    documentation = (
        "The person's employee pension contributions given relief, which the "
        "model takes as paid under a net pay arrangement. The employer "
        "deducts them from employment income (FA 2004 s.193(2)), so total "
        "income (ITA 2007 s.23 Step 1) is after them, up to that income: any "
        "excess is relieved on a claim at Step 2 (s.193(4) and (6)). Within "
        "the annual limit for relief (s.190), employee contributions are "
        "relieved before personal ones. The model gives the relief itself "
        "through allowances (pension_contributions_relief); this is the part "
        "of it that total income is already after."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Finance Act 2004 s. 193",
        href="https://www.legislation.gov.uk/ukpga/2004/12/section/193",
    )

    def formula(person, period, parameters):
        relieved_employee_contributions = min_(
            person("employee_pension_contributions", period),
            person("pension_contributions_relief", period),
        )
        return min_(
            relieved_employee_contributions,
            person("taxable_employment_income", period),
        )
