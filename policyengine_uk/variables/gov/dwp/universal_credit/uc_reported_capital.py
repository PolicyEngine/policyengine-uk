from policyengine_uk.model_api import *


class uc_reported_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "reported Universal Credit capital"
    documentation = (
        "Capital of the claimant and any partner as recorded for this benefit "
        "unit. Universal Credit assesses a couple's capital together (Welfare "
        "Reform Act 2012 s. 5; UC Regulations 2013 reg. 18(2)), which a "
        "benefit-unit capital record covers, so this is the benefit unit's "
        "recorded capital (benunit_reported_capital) unless set directly. "
        "When it is 0 or more it replaces the household proxy and the "
        "person-level sources in uc_assessable_capital, and the model applies "
        "no Schedule 10 disregard to it, so it must already be the countable "
        "figure. Any negative value, including -1 when nothing is recorded, "
        "means the household proxy applies. Set it to 0 to override the "
        "household proxy with zero assessable capital."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    default_value = -1
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/18",
    )

    def formula(benunit, period, parameters):
        return benunit("benunit_reported_capital", period)
