from policyengine_uk.model_api import *


class add_rate_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income at the higher rate"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 11D",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/11D",
    )
    unit = GBP

    def formula(person, period, parameters):
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
        other_income = person("earned_taxable_income", period)
        savings_deductions = add(
            person,
            period,
            [
                "received_allowances_savings_income",
                "savings_allowance",
                "savings_starter_rate_income",
            ],
        )
        savings_income_less_deductions = max_(
            0,
            person("taxable_savings_interest_income", period)
            - savings_deductions,
        )
        add_rate_amount_with = clip(
            other_income + savings_income_less_deductions,
            thresholds[2],
            inf,
        )
        add_rate_amount_without = clip(other_income, thresholds[2], inf)
        return max_(0, add_rate_amount_with - add_rate_amount_without)
