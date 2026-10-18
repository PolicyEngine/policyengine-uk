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
        "excess is relieved on a claim at Step 2 (s.193(4) and (6)). The "
        "annual limit for relief (s.190(1)) is the person's relevant UK "
        "earnings, which include all their employment income chargeable to "
        "tax, statutory sick and maternity pay among it (s.189(2)(a)), so it "
        "never holds the deduction below that income. Within the limit, the "
        "model relieves employee contributions before personal ones, so "
        "contributions relieved at source never change it. Nothing is "
        "relieved from age 75 (s.188(3)(a)). The model gives the relief "
        "itself through allowances (pension_contributions_relief). That "
        "counts only wages and trading profits as relevant UK earnings "
        "(issue #2371), so where statutory pay makes up part of the earnings "
        "it can give less relief than this deduction."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Finance Act 2004 s. 189",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/189",
        ),
        dict(
            title="Finance Act 2004 s. 190",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/190",
        ),
        dict(
            title="Finance Act 2004 s. 193",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/193",
        ),
    ]

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.pensions
        under_age_limit = (
            person("age", period) < p.pension_contributions_relief_age_limit
        )
        return under_age_limit * min_(
            person("employee_pension_contributions", period),
            person("taxable_employment_income", period),
        )
