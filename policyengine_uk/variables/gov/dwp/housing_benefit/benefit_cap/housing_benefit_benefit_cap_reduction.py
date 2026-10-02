from policyengine_uk.model_api import *


class housing_benefit_benefit_cap_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit benefit cap reduction"
    documentation = (
        "The reduction the benefit cap makes to Housing Benefit: the excess "
        "of the welfare benefits of the claimant or couple over the Housing "
        "Benefit cap, limited so that the claimant keeps the minimum amount "
        "of Housing Benefit, 50 pence a week (HB Regs 2006 regs. 75 and "
        "75D)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75",
    )

    def formula(benunit, period, parameters):
        excess = max_(
            benunit("benefit_cap_welfare_benefits", period)
            - benunit("housing_benefit_benefit_cap", period),
            0,
        )
        entitlement = benunit("housing_benefit_pre_benefit_cap", period)
        minimum = (
            parameters(period).gov.dwp.housing_benefit.minimum_weekly_amount
            * WEEKS_IN_YEAR
        )
        return min_(excess, max_(entitlement - minimum, 0))
