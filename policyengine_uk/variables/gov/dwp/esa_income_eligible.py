from policyengine_uk.model_api import *


class esa_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for income-related ESA after the capital test"
    documentation = (
        "Bounded capital-rule screen applied to reported income-related ESA "
        "awards. This is not a full entitlement model."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        ESA = parameters(period).gov.dwp.ESA.income
        capital = benunit("esa_income_assessable_capital", period)
        reported_award = add(benunit, period, ["esa_income_reported"]) > 0
        # Once one of the family's legacy benefits has closed, DWP's
        # migration notice ends this award too: a Universal Credit claim
        # brings the abolition of income-related ESA (Welfare Reform Act
        # 2012 s. 33(1)) into force for the claimant (see SI 2025/1148
        # art. 3A(3)), and a family that does not claim loses the award at the
        # notice's deadline (SI 2014/1230 reg 46(1)(a)).
        closed = benunit("legacy_benefits_closed", period) | benunit(
            "claims_uc_at_legacy_closure", period
        )
        return reported_award & ~closed & (capital <= ESA.capital.limit)
