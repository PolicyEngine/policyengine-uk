from policyengine_uk.model_api import *
from policyengine_uk.utils.pensions import annual_allowance_for_year


class pension_annual_allowance(Variable):
    value_type = float
    entity = Person
    label = "Annual Allowance for pension contributions"
    documentation = (
        "The standard annual allowance, tapered from 2016-17 only when both "
        "the statutory adjusted-income and threshold-income limits are "
        "exceeded. The reduction rounds down to whole pounds before applying "
        "the tapered minimum. See docs/engineering/pension-annual-allowance.md "
        "for income conventions and survey-data limitations."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2004/12/section/228ZA"

    def formula(person, period, parameters):
        return parameters(
            period
        ).gov.hmrc.income_tax.allowances.annual_allowance.default

    def formula_2016(person, period, parameters):
        return annual_allowance_for_year(
            person("pension_annual_allowance_adjusted_income", period),
            person("pension_annual_allowance_threshold_income", period),
            parameters(period).gov.hmrc.income_tax.allowances.annual_allowance,
            period.start.year,
        )
