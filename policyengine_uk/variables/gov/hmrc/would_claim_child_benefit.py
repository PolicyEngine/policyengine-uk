from policyengine_uk.model_api import *


class would_claim_child_benefit(Variable):
    label = "Would claim Child Benefit"
    documentation = (
        "Whether this benefit unit would claim Child Benefit if eligible"
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        takeup_rate = parameters(period).gov.hmrc.child_benefit.takeup
        overall_p = takeup_rate.overall
        return (random(benunit) < overall_p) * ~benunit(
            "child_benefit_opts_out", period
        )
