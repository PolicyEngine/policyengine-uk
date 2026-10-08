from policyengine_uk.model_api import *


class housing_benefit_pension_credit_earnings_disregard_assessment(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Earnings disregard already included in the Pension Credit assessment"
    documentation = (
        "Earnings deduction already made in the supplied Pension Credit "
        "net-income assessment, not an additional HB deduction. Override "
        "with the actual assessed amount when supplying that assessment. "
        "The fallback reads the model's pension_credit_earnings_disregard "
        "when that component is installed (PR #2019); otherwise it is zero "
        "because the existing model PC-income formula makes no such deduction. "
        "This explicit compatibility path avoids duplicating that separate PR."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )

    def formula(benunit, period, parameters):
        # Structural compatibility, not a branch on household values.
        if (
            "pension_credit_earnings_disregard"
            in benunit.simulation.tax_benefit_system.variables
        ):
            return benunit("pension_credit_earnings_disregard", period)
        return np.zeros(benunit.count)
