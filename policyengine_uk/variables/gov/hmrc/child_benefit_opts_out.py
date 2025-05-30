from policyengine_uk.model_api import *


class child_benefit_opts_out(Variable):
    label = "opts out of Child Benefit"
    documentation = (
        "Whether this family would opt out of receiving Child Benefit payments"
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        if benunit.simulation.dataset is not None:
            ani = benunit.members("adjusted_net_income", period)
            hmrc = parameters(period).gov.hmrc
            cb_hitc = hmrc.income_tax.charges.CB_HITC
            cb = hmrc.child_benefit
            in_phase_out = ani > cb_hitc.phase_out_end
            return where(
                benunit.any(in_phase_out),
                random(benunit) < cb.opt_out_rate,
                False,
            )
        else:
            # If we're not in a microsimulation, assume the family would not opt out
            return False
