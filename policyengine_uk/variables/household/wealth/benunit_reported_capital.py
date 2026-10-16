from policyengine_uk.model_api import *


class benunit_reported_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "reported benefit unit capital"
    documentation = (
        "Savings and investments of the benefit unit's adults (the claimant "
        "and any partner) as recorded, such as the Family Resources Survey's "
        "benefit-unit financial total (finite nonnegative TOTCAPB4, otherwise "
        "finite nonnegative TOTCAPB3, otherwise -1). The data loader selects "
        "that total once, without summing claimant and partner totals again. "
        "This financial observation excludes property. Universal Credit uses "
        "it instead of financial savings, investments and covered Lifetime "
        "ISA proxies, while retaining countable property separately. Pension "
        "Credit retains its existing treatment via pension_credit_reported_capital. "
        "Survey financial totals approximate countable financial capital: "
        "asset-specific disregards and valuations are not observed. Supply "
        "uc_reported_capital directly for a complete UC countable-capital "
        "override. A value set for one year is uprated into later years. Any "
        "negative value, including the default -1, means none is recorded, "
        "and each means test falls back to its household capital proxy. 0 "
        "records no financial capital."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    default_value = -1
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
