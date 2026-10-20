from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income._net_earnings import (
    person_net_earnings,
)


class council_tax_reduction_net_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction net earnings"
    documentation = (
        "Net earnings of the claimant and partner, from which the pensioner "
        "Council Tax Reduction earnings disregards are taken. The earnings and "
        "deductions are those of housing_benefit_net_earnings, except the "
        "share of pension contributions, which is the scheme's own "
        "(council_tax_reduction_pension_contribution_deduction_rate): "
        "SI 2012/2885 Sch 1 para 19(2)(b)-(c), WSI 2013/3029 Sch 1 para "
        "13(2)(b)-(c) and SSI 2012/319 reg 33(2)(b)-(c) each deduct one-half "
        "and do not refer to Housing Benefit's share."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/19",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/29",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/13",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/23",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/33",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/36",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        rate = benunit(
            "council_tax_reduction_pension_contribution_deduction_rate", period
        )
        net_earnings = person_net_earnings(person, period, benunit.project(rate))
        # The claimant and partner, as for Housing Benefit.
        claimant_or_partner = person("is_claimant_or_partner", period)
        return benunit.sum(net_earnings * claimant_or_partner)
