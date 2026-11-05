from policyengine_uk.model_api import *


class free_tv_licence_value(Variable):
    label = "free TV licence value"
    documentation = (
        "Value included in HBAI income for the share of the year covered by "
        "the complete age-based exemption. The blind discount is excluded."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/21/section/363",
        "https://www.legislation.gov.uk/ukpga/2003/21/section/365A",
        "https://www.legislation.gov.uk/uksi/2016/704/regulation/9/made",
        "https://www.legislation.gov.uk/uksi/2026/104/made",
        "https://www.gov.uk/free-discount-tv-licence",
        "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025",
    )

    def formula(household, period, parameters):
        licence_required = household("tv_licence_required", period)
        free_licence_share = household(
            "tv_licence_free_licence_share",
            period,
        )
        would_evade = household("would_evade_tv_licence_fee", period)
        fee = parameters(period).gov.dcms.bbc.tv_licence.colour
        return (licence_required & ~would_evade) * fee * free_licence_share
