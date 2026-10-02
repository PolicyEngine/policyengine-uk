from policyengine_uk.model_api import *


class pension_contributions_relief(Variable):
    value_type = float
    entity = Person
    label = "Reduction in taxable income from pension contributions"
    documentation = (
        "Relief on the individual's own pension contributions, up to their "
        "relevant UK earnings. It is never negative: with no contributions, "
        "no earnings, or a self-employment loss, the relief is at least zero."
    )
    definition_period = YEAR
    reference = dict(
        title="Finance Act 2004 s. 188-194",
        href="https://www.legislation.gov.uk/ukpga/2004/12/section/188",
    )
    unit = GBP

    def formula(person, period, parameters):
        contributions = max_(0, person("pension_contributions", period))
        pension_allowance = person("pension_annual_allowance", period)
        age_limit = parameters(
            period
        ).gov.hmrc.pensions.pension_contributions_relief_age_limit
        earnings = person("relevant_uk_earnings", period)
        under_age_limit = person("age", period) < age_limit
        basic_amount = parameters(
            period
        ).gov.hmrc.income_tax.reliefs.pension_contribution.basic_amount
        tax_relief = min_(earnings, contributions) * under_age_limit
        max_pension_relief = max_(basic_amount, pension_allowance)

        return max_(0, min_(tax_relief, max_pension_relief))
