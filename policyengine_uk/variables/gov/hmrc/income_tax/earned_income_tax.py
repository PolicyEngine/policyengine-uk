from policyengine_uk.model_api import *


class earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on earned income"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 10",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/10",
    )
    unit = GBP

    def formula(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        return rates.uk.calc(person("earned_taxable_income", period))

    def formula_2017_04_06(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        uk_amount = rates.uk.calc(person("earned_taxable_income", period))
        scot_amount = rates.scotland.pre_starter_rate.calc(
            person("earned_taxable_income", period)
        )
        return where(scot, scot_amount, uk_amount)

    def formula_2018_04_06(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        uk_amount = rates.uk.calc(person("earned_taxable_income", period))
        scot_amount = rates.scotland.post_starter_rate.calc(
            person("earned_taxable_income", period)
        )
        return where(scot, scot_amount, uk_amount)