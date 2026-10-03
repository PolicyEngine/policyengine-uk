from policyengine_uk.model_api import *


class uc_trading_losses_set_against_profits(Variable):
    value_type = float
    entity = Person
    label = "Trading losses set against other trades' profits for Universal Credit"
    documentation = (
        "UC Regs 2013 reg 57(2) Steps 1-2 add together the profit or loss of "
        "each of the person's trades, and Step 3 makes a negative total nil: "
        "one trade's loss reduces another trade's profits but never employed "
        "earnings. Over a year, with profits and losses spread evenly, that is "
        "the loss up to the profits. UC earnings and the benefit cap earnings "
        "test (reg 82) both deduct it."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Universal Credit Regulations 2013 reg. 57(2)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
    )

    def formula(person, period, parameters):
        return min_(
            person("trading_loss", period), person("self_employment_income", period)
        )
