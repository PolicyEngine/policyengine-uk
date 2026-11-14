from policyengine_uk.model_api import *


class uc_trading_losses_set_against_profits(Variable):
    value_type = float
    entity = Person
    label = "Trading losses set against other trades' profits for Universal Credit"
    documentation = (
        "UC Regs 2013 reg 57(2) Steps 1-2 add together the profit or loss of "
        "each of the person's trades; the final nil floor ensures that "
        "one trade's loss reduces another trade's profits but never employed "
        "earnings. Company earnings treated as self-employed under reg 77(3)(b) "
        "join that total, including a negative company result. Over a year, "
        "with profits and losses spread evenly, relief is the loss up to the "
        "positive combined trade result. UC earnings and the benefit cap earnings "
        "test (reg 82) both deduct it. This annual approximation does not "
        "track unused losses by assessment period under reg 57A; prior-period "
        "losses must not be entered as a fresh current-year trading_loss."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 57(2)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 77(3)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 57A (assessment-period losses)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57A",
        ),
    ]

    def formula(person, period, parameters):
        combined_trade_result = person("self_employment_income", period) + person(
            "uc_company_self_employed_earnings", period
        )
        return min_(person("trading_loss", period), max_(0, combined_trade_result))
