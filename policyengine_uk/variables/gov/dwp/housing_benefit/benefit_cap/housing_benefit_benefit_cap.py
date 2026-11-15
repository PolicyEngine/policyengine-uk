from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_cap import benefit_cap_annual_limit


class housing_benefit_benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit benefit cap"
    documentation = (
        "The applicable annual limit on the welfare benefits of a Housing "
        "Benefit claimant or couple (HB Regs 2006 reg. 75CA(2)), or infinity "
        "where the cap does not apply: an exception in regulation 75E or 75F "
        "(reg. 75A), or a claim under the pension-age regulations, which have "
        "no benefit cap. The weekly relevant amount (the annual limit divided "
        "by 52, rounded to the nearest penny: reg. 75CA(1)) is not rounded: "
        "the model applies the annual limit."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75A",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75CA",
    )

    def formula(benunit, period, parameters):
        limit = benefit_cap_annual_limit(
            benunit,
            period,
            parameters,
            benunit("is_housing_benefit_benefit_cap_single_claimant_rate", period),
        )
        exempt = benunit("is_housing_benefit_benefit_cap_exempt", period)
        return where(exempt, np.inf, limit)
