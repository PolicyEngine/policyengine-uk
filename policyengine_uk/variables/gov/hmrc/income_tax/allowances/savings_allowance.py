from policyengine_uk.model_api import *


class savings_allowance(Variable):
    value_type = float
    entity = Person
    label = "Savings Allowance for the year"
    documentation = (
        "The Personal Savings Allowance (ITA 2007 s. 12B): the basic amount "
        "with no higher-rate income, the higher amount with higher-rate but "
        "no additional-rate income, and the additional amount (nil) with any "
        "additional-rate income. For a Scottish or Welsh taxpayer, s. "
        "12B(8)(a)(iv) and (b)(iv) count as higher- or additional-rate income "
        "what would be charged at those rates if they were not a Scottish or "
        "Welsh taxpayer, so the bands are the rest-of-UK ones for everyone. "
        "tax_band follows the Scottish bands for a Scottish taxpayer, as the "
        "Marriage Allowance conditions need, so it is not read here. Taxable "
        "income is taken, as in tax_band, as net income less allowances, and "
        "a Gift Aid gift raises the basic and higher rate limits by its "
        "grossed-up amount (ITA 2007 s. 414(2)(b))."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2007/3/section/12B"
    unit = GBP

    def formula(person, period, parameters):
        income_tax = parameters(period).gov.hmrc.income_tax
        amounts = income_tax.allowances.personal_savings_allowance
        thresholds = income_tax.rates.uk.thresholds
        # Net income, not adjusted net income: adjusted net income deducts
        # the grossed-up Gift Aid gift (s. 58), which instead raises the rate
        # limits (s. 414(2)(b)) that decide the band.
        taxable_income = person("net_income", period) - person("allowances", period)
        gross_gift = person("gift_aid_grossed_up", period)
        basic_rate_limit = thresholds[1] + gross_gift
        higher_rate_limit = thresholds[2] + gross_gift
        # Income up to a limit is charged at the lower rate and only income
        # above it at the higher one (ITA 2007 s. 10(2)-(3)), so taxable
        # income exactly at a limit has none in the band above.
        return select(
            [taxable_income > higher_rate_limit, taxable_income > basic_rate_limit],
            [amounts.additional, amounts.higher],
            default=amounts.basic,
        )
