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
        "income is taken, as in tax_band, as adjusted net income less "
        "allowances."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2007/3/section/12B"
    unit = GBP

    def formula(person, period, parameters):
        income_tax = parameters(period).gov.hmrc.income_tax
        amounts = income_tax.allowances.personal_savings_allowance
        thresholds = income_tax.rates.uk.thresholds
        taxable_income = person("adjusted_net_income", period) - person(
            "allowances", period
        )
        # thresholds[1] is the basic rate limit and thresholds[2] the higher
        # rate limit. Income up to a limit is charged at the lower rate and
        # only income above it at the higher one (ITA 2007 s. 10(2)-(3)), so
        # taxable income exactly at a limit has none in the band above.
        return select(
            [taxable_income > thresholds[2], taxable_income > thresholds[1]],
            [amounts.additional, amounts.higher],
            default=amounts.basic,
        )
