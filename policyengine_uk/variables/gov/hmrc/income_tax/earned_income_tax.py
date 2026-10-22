from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax import (
    calc_income_tax_with_gift_aid,
    first_extended_scottish_threshold,
)


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
        income = person("earned_taxable_income", period)
        gross_gift = person("gift_aid_grossed_up", period)
        return where(
            person("pays_scottish_income_tax", period),
            calc_income_tax_with_gift_aid(
                rates.scotland.rates,
                income,
                gross_gift,
                first_extended_scottish_threshold(rates.scotland.rates),
                len(rates.scotland.rates.thresholds),
            ),
            calc_income_tax_with_gift_aid(rates.uk, income, gross_gift),
        )
