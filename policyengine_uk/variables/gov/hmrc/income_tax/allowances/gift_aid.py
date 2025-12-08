from policyengine_uk.model_api import *


class gift_aid(Variable):
    value_type = float
    entity = Person
    label = "Expenditure under Gift Aid"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007, Part 8 Chapter 2 (Gift Aid)",
        href="https://www.legislation.gov.uk/ukpga/2007/3/part/8/chapter/2",
    )


class gift_aid_grossed_up(Variable):
    value_type = float
    entity = Person
    label = "Gift Aid grossed up by basic rate"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007, s. 58 (2)",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/58",
    )

    def formula(person, period, parameters):
        gift_aid = person("gift_aid", period)
        basic_rate = parameters(period).gov.hmrc.income_tax.rates.uk.rates[0]
        # Grossed up amount = gift_aid / (1 - basic_rate)
        # With basic_rate = 0.2: gift_aid / 0.8 = gift_aid * 1.25
        return gift_aid / (1 - basic_rate)
