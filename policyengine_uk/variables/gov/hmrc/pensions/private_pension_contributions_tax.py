from policyengine_uk.model_api import *


class personal_pension_contributions_tax(Variable):
    value_type = float
    entity = Person
    label = "Reduction in taxable income from pension contributions to pensions other than the State Pension"
    definition_period = YEAR
    reference = dict(
        title="Finance Act 2004 s. 227",
        href="https://www.legislation.gov.uk/ukpga/2004/12/section/227",
    )
    unit = GBP

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax.rates.uk
        taxed_income = person("taxed_income", period)

        personal_pension_contributions = person(
            "employee_pension_contributions", period
        ) + person("personal_pension_contributions", period)
        pension_annual_allowance = person("pension_annual_allowance", period)
        taxable_contributions = (
            personal_pension_contributions - pension_annual_allowance
        )

        tax_rate = p.marginal_rates(taxed_income)
        return max_(0, taxable_contributions * tax_rate)
