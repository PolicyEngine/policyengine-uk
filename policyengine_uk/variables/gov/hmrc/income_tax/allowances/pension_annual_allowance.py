from policyengine_uk.model_api import *


def _tapered_allowance(person, period, allowance, reduction_rate):
    adjusted = person("pension_annual_allowance_adjusted_income", period)
    threshold = person("pension_annual_allowance_threshold_income", period)
    # s. 228ZA(3)(b) derives the threshold limit from the standard allowance.
    high_income = (adjusted > allowance.taper) & (
        threshold > allowance.taper - allowance.default
    )
    reduction = np.floor(max_(0, adjusted - allowance.taper) * reduction_rate)
    return where(
        high_income,
        max_(allowance.minimum, allowance.default - reduction),
        allowance.default,
    )


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
        allowance = parameters(period).gov.hmrc.income_tax.allowances.annual_allowance
        # Original s. 228ZA(1): (A - £10,000) / £60,000, equal to one half
        # at the statutory £40,000 standard allowance.
        rate = (allowance.default - allowance.minimum) / allowance.taper_income_range
        return _tapered_allowance(person, period, allowance, rate)

    def formula_2020(person, period, parameters):
        allowance = parameters(period).gov.hmrc.income_tax.allowances.annual_allowance
        return _tapered_allowance(person, period, allowance, allowance.reduction_rate)
