from policyengine_uk.model_api import *


class jsa_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for income-based JSA after the capital test"
    documentation = (
        "Bounded capital-rule screen applied to reported income-based JSA awards. "
        "This is not a full entitlement model."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        JSA = parameters(period).gov.dwp.JSA.income
        capital = benunit("jsa_income_assessable_capital", period)
        reported_award = add(benunit, period, ["jsa_income_reported"]) > 0
        # Once one of the family's legacy benefits has closed, DWP's
        # migration notice ends this award too: a Universal Credit claim
        # brings the abolition of income-based JSA (Welfare Reform Act
        # 2012 s. 33(1)) into force for the claimant (see SI 2025/1148
        # art. 3A(3)), and a family that does not claim loses the award at the
        # notice's deadline (SI 2014/1230 reg 46(1)(a)).
        closed = benunit("legacy_benefits_closed", period)
        return reported_award & ~closed & (capital <= JSA.capital.limit)
