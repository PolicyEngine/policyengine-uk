from policyengine_uk.model_api import *


class basic_rate_savings_income_pre_starter(Variable):
    value_type = float
    entity = Person
    label = "Savings income which would otherwise be taxed at the basic rate, without the starter rate"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007, s. 12",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/12",
    )

    def formula(person, period, parameters):
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
        savings_income = max_(
            0,
            person("taxable_savings_interest_income", period)
            - person("received_allowances_savings_income", period),
        )
        other_income = person("earned_taxable_income", period)
        basic_rate_amount_with_savings = clip(
            savings_income + other_income,
            thresholds[0],
            thresholds[1],
        )
        basic_rate_amount_without_savings = clip(
            other_income, thresholds[0], thresholds[1]
        )
        return basic_rate_amount_with_savings - basic_rate_amount_without_savings
