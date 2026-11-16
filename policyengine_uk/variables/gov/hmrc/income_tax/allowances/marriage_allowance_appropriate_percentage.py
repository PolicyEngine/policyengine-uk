from policyengine_uk.model_api import *


class marriage_allowance_appropriate_percentage(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance appropriate percentage"
    documentation = (
        "The rate of the Marriage Allowance tax reduction: the basic rate, or "
        "for a Scottish taxpayer the Scottish basic rate, whatever rates the "
        "person's income bears (ITA 2007 s. 55B(3)). The Scottish rates of "
        "s. 11A start in 2016-17, so before then the formula gives a Scottish "
        "taxpayer the basic rate. Section 55B(3) gives a Welsh taxpayer the "
        "Welsh basic rate, but the model has no Welsh rates, so a Welsh "
        "taxpayer takes the basic rate."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007 s. 55B(3)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
        ),
        dict(
            title="Scottish Parliament motion S6M-16531 (2025-26 Scottish rates)",
            href="https://www.parliament.scot/chamber-and-committees/votes-and-motions/S6M-16531",
        ),
    ]
    unit = "/1"

    def formula(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        basic_rate = rates.uk.rates[0]
        if period.start.year < 2016:
            return basic_rate
        # The Scottish basic rate band is the second band of the Scottish
        # scale in every year: before 2018-19 the first band (the starter
        # rate) has no values. Read that band itself rather than an index into
        # the rates in force at the instant, which would move if a reform
        # removed the starter rate.
        scottish_bands = parameters.gov.hmrc.income_tax.rates.scotland.rates
        scottish_basic_rate = scottish_bands.brackets[1].rate(period.start)
        return where(
            person("pays_scottish_income_tax", period),
            scottish_basic_rate,
            basic_rate,
        )
