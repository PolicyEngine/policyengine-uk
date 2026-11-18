from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax import taxable_savings_income_in_band


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
        income_tax = parameters(period).gov.hmrc.income_tax
        thresholds = income_tax.rates.uk.thresholds
        # ITA 2007 s.414(2)(b): extend both UK rate limits by the gross gift.
        gross_gift = person("gift_aid_grossed_up", period)
        return taxable_savings_income_in_band(
            person,
            period,
            income_tax,
            thresholds[2] + gross_gift,
            inf,
        )
