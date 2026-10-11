from policyengine_uk.model_api import *


class pension_credit_reported_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "reported Pension Credit capital"
    documentation = (
        "Countable capital of the claimant and partner as recorded for this "
        "benefit unit. Pension Credit counts the claimant's capital, and the "
        "State Pension Credit Act 2002 s. 5 treats the partner's as the "
        "claimant's, which a benefit-unit capital record covers, so this is "
        "the benefit unit's recorded capital (benunit_reported_capital) unless "
        "set directly. When this is 0 or more it replaces every capital source "
        "in Pension Credit assessable capital: the household proxy (savings, "
        "land, property and corporate_wealth) and the person-level sources such "
        "as a Lifetime ISA. The model applies neither the Schedule V disregards "
        "nor the reg. 19 valuation to it, so it must already be the countable "
        "figure, and reforms to the capital source parameters do not reach a "
        "benefit unit that records it. Any negative value, including -1 when "
        "nothing is recorded, means the household proxy applies. 0 records no "
        "capital."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    default_value = -1
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/5"

    def formula(benunit, period, parameters):
        return benunit("benunit_reported_capital", period)
