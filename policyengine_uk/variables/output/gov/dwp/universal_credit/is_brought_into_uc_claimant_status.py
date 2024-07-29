from policyengine_uk.model_api import *


class is_brought_into_uc_claimant_status(Variable):
    label = "brought into Universal Credit claimant status"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        if benunit.simulation.baseline is None:
            return False
        uc_entitled = benunit("is_uc_entitled", period)
        uc_entitled_baseline = benunit("is_uc_entitled_baseline", period)
        takeup = parameters(period).gov.dwp.universal_credit.takeup
        takes_up_given_new_claimant = random(benunit) < takeup
        return (
            uc_entitled & ~uc_entitled_baseline & takes_up_given_new_claimant
        )
