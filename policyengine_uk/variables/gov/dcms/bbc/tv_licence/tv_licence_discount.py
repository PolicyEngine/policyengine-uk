from policyengine_uk.model_api import *


class tv_licence_discount(Variable):
    label = "TV licence discount"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/21/section/365A",
        "https://www.tvlicensing.co.uk/reducedfee",
    )

    def formula(household, period, parameters):
        person = household.members
        tv_licence = parameters(period).gov.dcms.bbc.tv_licence
        free_licence_share = household(
            "tv_licence_free_licence_share",
            period,
        )

        # Blind discount
        is_blind = person("is_blind", period)
        has_blind = household.any(is_blind)
        blind_discount = has_blind * tv_licence.discount.blind.discount

        return free_licence_share + (1 - free_licence_share) * blind_discount
