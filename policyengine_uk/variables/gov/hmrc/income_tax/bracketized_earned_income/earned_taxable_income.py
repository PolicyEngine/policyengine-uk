from policyengine_uk.model_api import *


class earned_taxable_income(Variable):
    value_type = float
    entity = Person
    label = "Non-savings, non-dividend income for Income Tax"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 10",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/10",
    )
    unit = GBP

    def formula(person, period, parameters):
        exclusion_list = parameters(
            period
        ).gov.hmrc.income_tax.earned_taxable_income_exclusions
        ani = person("adjusted_net_income", period)
        exclusions = add(person, period, exclusion_list)
        return max_(0, ani - exclusions)
