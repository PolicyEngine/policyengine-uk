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
        savings_after_allowances = max_(
            0,
            person("taxable_savings_interest_income", period)
            - person("received_allowances_savings_income", period),
        )
        zero_rate_savings = min_(
            savings_after_allowances,
            person("savings_starter_rate_income", period)
            + person("savings_allowance", period),
        )
        taxable_savings_start = other_income + zero_rate_savings
        add_rate_amount_with = clip(
            other_income + savings_after_allowances,
            thresholds[2],
            inf,
        )
        add_rate_amount_without = clip(taxable_savings_start, thresholds[2], inf)
        return max_(0, add_rate_amount_with - add_rate_amount_without)
