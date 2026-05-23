from policyengine_uk.model_api import *


class ipswich_council_tax_reduction_uc_weekly_contribution(Variable):
    value_type = float
    entity = BenUnit
    label = "Ipswich Council Tax Reduction weekly contribution for Universal Credit claimants"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.ipswich.gov.uk/sites/ipswich/files/2026-03/Council%20Tax%20Reduction%20scheme%202026_0.pdf"

    def formula(benunit, period, parameters):
        contribution = parameters(
            period
        ).gov.local_authorities.ipswich.council_tax_reduction.uc_earnings_contribution
        monthly_uc_earnings = benunit(
            "ipswich_council_tax_reduction_uc_monthly_earnings", period
        )
        return contribution.amount.calc(monthly_uc_earnings)
