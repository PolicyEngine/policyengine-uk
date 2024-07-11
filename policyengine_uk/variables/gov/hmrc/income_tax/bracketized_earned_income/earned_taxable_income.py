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
        EXCLUSIONS = [
            "taxable_savings_interest_income",
            "taxable_dividend_income",
            "allowances",
            "marriage_allowance",
            "pension_contributions_relief",
        ]
        ANI = person("adjusted_net_income", period)
        exclusions = add(person, period, EXCLUSIONS)
        return max_(0, ANI - exclusions)