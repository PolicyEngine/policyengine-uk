from policyengine_uk.model_api import *


class babergh_council_tax_reduction_uc_weekly_contribution(Variable):
    value_type = float
    entity = BenUnit
    label = "Babergh Council Tax Reduction weekly contribution for Universal Credit claimants"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.babergh.gov.uk/documents/d/babergh/bdc-ctr-scheme-2026_27-v4-pdf"
    )

    def formula(benunit, period, parameters):
        contribution = parameters(
            period
        ).gov.local_authorities.babergh.council_tax_reduction.uc_earnings_contribution
        monthly_uc_earnings = benunit(
            "babergh_council_tax_reduction_uc_monthly_earnings", period
        )
        return contribution.amount.calc(monthly_uc_earnings)
