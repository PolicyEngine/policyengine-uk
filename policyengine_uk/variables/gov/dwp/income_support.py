from policyengine_uk.model_api import *


class income_support(Variable):
    value_type = float
    entity = BenUnit
    label = "Income Support"
    definition_period = YEAR
    unit = GBP
    defined_for = "would_claim_IS"

    def formula(benunit, period, parameters):
        if not parameters(period).gov.dwp.income_support.active:
            return benunit.empty_array()
        # Once one of the family's legacy benefits has closed, DWP's
        # migration notice ends this award too: on a Universal Credit claim
        # (SI 2014/1230 reg 8(2A)) or at the notice's deadline (reg 46(1)(a)).
        closed = benunit("legacy_benefits_closed", period)
        return where(closed, 0, benunit("income_support_entitlement", period))
