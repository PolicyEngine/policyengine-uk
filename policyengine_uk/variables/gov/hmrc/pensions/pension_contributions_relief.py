from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import supplied_input


class pension_contributions_relief(Variable):
    value_type = float
    entity = Person
    label = "Reduction in taxable income from pension contributions"
    definition_period = YEAR
    reference = dict(
        title="Finance Act 2004 s. 188-194",
        href="https://www.legislation.gov.uk/ukpga/2004/12/section/188",
    )
    unit = GBP

    def formula(person, period, parameters):
        contributions = person("pension_contributions", period)
        age_limit = parameters(
            period
        ).gov.hmrc.pensions.pension_contributions_relief_age_limit
        income = add(person, period, ["employment_income", "self_employment_income"])
        under_age_limit = person("age", period) < age_limit
        basic_amount = parameters(
            period
        ).gov.hmrc.income_tax.reliefs.pension_contribution.basic_amount
        tax_relief = min_(income, contributions) * under_age_limit
        supplied_ani = supplied_input(person, "adjusted_net_income", period)
        if supplied_ani is not None:
            # The existing AA cap depends on net_income, which restores this
            # relief to a supplied ANI. Solve the cap without that cycle:
            # r = min(eligible, cap(A + r)), where A = ANI + gross Gift Aid.
            allowance = parameters(
                period
            ).gov.hmrc.income_tax.allowances.annual_allowance
            income_before_relief = supplied_ani + person("gift_aid_grossed_up", period)
            max_pension_relief = max_(
                max_(basic_amount, allowance.minimum),
                allowance.default
                - allowance.reduction_rate
                * max_(0, income_before_relief + allowance.default - allowance.taper)
                / (1 + allowance.reduction_rate),
            )
        else:
            pension_allowance = person("pension_annual_allowance", period)
            max_pension_relief = max_(basic_amount, pension_allowance)

        return min_(tax_relief, max_pension_relief)
