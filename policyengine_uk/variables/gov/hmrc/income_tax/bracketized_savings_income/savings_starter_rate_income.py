from policyengine_uk.model_api import *


class savings_starter_rate_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income which is tax-free under the starter rate"
    documentation = (
        "Savings within the annual starting-rate band left after taxable "
        "non-savings income, including property income. The non-savings "
        "base already reflects allowance deductions; dividends sit above "
        "savings and do not directly reduce the starting-rate band."
    )
    definition_period = YEAR
    reference = list(
        [
            dict(
                title="Income Tax Act 2007, s. 12 (1) and (5)",
                href="https://www.legislation.gov.uk/ukpga/2007/3/section/12",
            ),
            dict(
                title="Income Tax Act 2007, s. 16 (3) and (5)",
                href="https://www.legislation.gov.uk/ukpga/2007/3/section/16",
            ),
            dict(
                title="Tax on savings interest",
                href="https://www.gov.uk/apply-tax-free-interest-on-savings/how-much-is-tax-free",
            ),
        ]
    )
    unit = GBP

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax
        limit = p.rates.savings_starter_rate.allowance
        phase_out_rate = p.rates.savings_starter_rate.phase_out

        savings_income = min_(
            person("basic_rate_savings_income_pre_starter", period),
            max_(
                0,
                person("taxable_savings_interest_income", period)
                - person("received_allowances_savings_income", period),
            ),
        )
        # ITA 2007 ss.12(5) and16 put taxable non-savings income below
        # savings. This base already reflects allowances, so every pound
        # reduces the starting band without deducting the PA again.
        non_savings_taxable_income = person("non_savings_taxable_income", period)

        removed_amount = max_(0, non_savings_taxable_income * phase_out_rate)

        post_taper_max = max_(0, limit - removed_amount)

        return clip(savings_income, 0, post_taper_max)
