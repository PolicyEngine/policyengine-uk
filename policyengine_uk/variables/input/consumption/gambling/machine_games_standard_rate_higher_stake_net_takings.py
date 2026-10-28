from policyengine_uk.model_api import *


class machine_games_standard_rate_higher_stake_net_takings(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    label = "Attributed higher-stake part of standard-rate machine games net takings"
    documentation = (
        "The part of machine_games_standard_rate_net_takings that comes from "
        "machines with a maximum charge to play above GBP 1 or a maximum prize "
        "above GBP 100. Under the Gambling Commission's stake and prize limits "
        "these are the Category B machines (B1 to B4). This input is a subset "
        "of the standard-rate input, not an addition to it: the duty caps it "
        "at that input. Machine Games Duty charges it at the standard rate "
        "until 31 March 2027 and at the higher rate from 1 April 2027."
    )
    reference = (
        "https://www.gov.uk/government/publications/budget-2026-overview-of-tax-legislation-and-rates-ootlar/budget-2026-overview-of-tax-legislation-and-rates-ootlar",
        "https://assets.publishing.service.gov.uk/media/6ae1883fe4367e5c8b0467df/AB26_Policy_Costing.pdf#page=67",
        "https://www.legislation.gov.uk/ukpga/2012/14/schedule/24/paragraph/5",
    )
