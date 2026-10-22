from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_cap import benefit_cap_annual_limit


class uc_benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit benefit cap"
    documentation = (
        "The applicable annual limit on the welfare benefits of a Universal "
        "Credit claimant or couple (UC Regs 2013 reg. 80A(2)), or infinity "
        "where regulation 82 or 83 lifts the cap (reg. 79(1))."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/79",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/80A",
    )

    def formula(benunit, period, parameters):
        limit = benefit_cap_annual_limit(
            benunit,
            period,
            parameters,
            benunit("is_uc_benefit_cap_single_claimant_rate", period),
        )
        exempt = benunit("is_uc_benefit_cap_exempt", period)
        return where(exempt, np.inf, limit)
