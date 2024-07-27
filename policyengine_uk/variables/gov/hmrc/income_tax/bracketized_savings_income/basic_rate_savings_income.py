from policyengine_uk.model_api import *


class basic_rate_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income at the basic rate"
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
        basic_rate_amount_with = clip(
            other_income + savings_income_less_deductions,
            thresholds[0],
            thresholds[1],
        )
        basic_rate_amount_without = clip(
            other_income, thresholds[0], thresholds[1]
        )
        return max_(0, basic_rate_amount_with - basic_rate_amount_without)
