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
    documentation = (
        "Earned taxable income uses the UK main scale before 2017-18. "
        "From 2017-18, Scottish taxpayers use the Scottish scale and other "
        "UK taxpayers use the UK main scale. Gift Aid extends the "
        "applicable tax bands."
    )
    reference = (
        dict(
            title="Income Tax Act 2007, s. 10",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/10",
        ),
        dict(
            title="Income Tax Act 2007, s. 11A as at 6 April 2016",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/11A/2016-04-06",
        ),
        dict(
            title=(
                "The Scotland Act 2012, Section 25 (Appointed Years) Order 2015, art. 3"
            ),
            href="https://www.legislation.gov.uk/uksi/2015/2000/article/3/made",
        ),
        dict(
            title="Scottish Rate of Income Tax Resolution 2016-17 (S4M-15497)",
            href="https://www.parliament.scot/chamber-and-committees/official-report/"
            "search-what-was-said-in-parliament/meeting-of-parliament-11-02-2016"
            "?iob=95367&meeting=10365",
        ),
    )
    unit = GBP

    def formula(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        income = person("earned_taxable_income", period)
        gross_gift = person("gift_aid_grossed_up", period)
        return calc_income_tax_with_gift_aid(rates.uk, income, gross_gift)

    def formula_2017(person, period, parameters):
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
