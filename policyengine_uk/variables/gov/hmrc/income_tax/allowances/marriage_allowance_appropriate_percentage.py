from policyengine_uk.model_api import *


class marriage_allowance_appropriate_percentage(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance appropriate percentage"
    documentation = (
        "The rate at which the Marriage Allowance reduces the gaining party's "
        "tax: the basic rate, or the Scottish basic rate for a Scottish "
        "taxpayer, whatever rate their income is actually taxed at. The Welsh "
        "basic rate equals the basic rate in this model."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007 s. 55B(3)",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
    )
    unit = "/1"

    def formula(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        # The Scottish basic rate follows the starter rate; before 2018-19 the
        # Scottish scale had no starter rate.
        scottish = rates.scotland.rates.rates
        scottish_basic = scottish[1 if len(scottish) > 3 else 0]
        return where(
            person("pays_scottish_income_tax", period),
            scottish_basic,
            rates.uk.rates[0],
        )
