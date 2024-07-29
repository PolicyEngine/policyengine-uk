from policyengine_uk.model_api import *


class savings_starter_rate_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income which is tax-free under the starter rate"
    definition_period = YEAR
    reference = list(
        [
            dict(
                title="Income Tax Act 2007, s. 12",
                href="https://www.legislation.gov.uk/ukpga/2007/3/section/12",
            ),
            dict(
                title="Tax on savings interest",
                href="https://www.gov.uk/apply-tax-free-interest-on-savings",
            ),
        ]
    )
    unit = GBP

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax
        limit = p.rates.savings_starter_rate.allowance
        phase_out_rate = p.rates.savings_starter_rate.phase_out

        max_personal_allowance = p.allowances.personal_allowance.amount

        starter_rate_taper_start = max_personal_allowance + limit

        savings_income = person(
            "basic_rate_savings_income_pre_starter", period
        )
        earned_taxable_income = person("earned_taxable_income", period)
        dividend_income = person("taxable_dividend_income", period)
        non_savings_income = earned_taxable_income + dividend_income

        removed_amount = max_(
            0, (non_savings_income - starter_rate_taper_start) * phase_out_rate
        )

        post_taper_max = max_(0, limit - removed_amount)

        return clip(savings_income, 0, post_taper_max)
