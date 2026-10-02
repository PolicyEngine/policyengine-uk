from policyengine_uk.model_api import *


class adjusted_total_income(Variable):
    value_type = float
    entity = Person
    label = "Adjusted total income"
    documentation = (
        "The base of the cap on reliefs against general income (ITA 2007 "
        "s.24A(8)): total income, plus payroll giving, less pension "
        "contributions given relief at source or under net pay or claim "
        "(FA 2004 ss.192, 193(4), 194(1)). The model deducts the person's own "
        "pension contributions as made, because its relief variable depends "
        "on adjusted net income through the tapered annual allowance, and "
        "does not model payroll giving."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 24A",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/24A",
    )

    def formula(person, period, parameters):
        return max_(
            0,
            person("total_income", period) - person("pension_contributions", period),
        )
