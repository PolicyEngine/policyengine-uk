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

        return where(
            person("pays_scottish_income_tax", period),
            rates.scotland.rates.calc(person("earned_taxable_income", period)),
            rates.uk.calc(person("earned_taxable_income", period)),
        )
