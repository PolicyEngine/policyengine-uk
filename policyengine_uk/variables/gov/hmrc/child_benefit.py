from policyengine_uk.model_api import *
from policyengine_uk.utils.child_benefit import child_benefit_charge_share


class child_benefit(Variable):
    label = "Child Benefit"
    documentation = (
        "Total Child Benefit paid to a benefit unit that would claim it. "
        "Claimants with payment opt-outs resume when the charge share falls below "
        "the assumed opt-out threshold; an opt-out flag never establishes a claim."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    category = BENEFIT
    defined_for = "would_claim_child_benefit"
    reference = "https://www.gov.uk/child-benefit-tax-charge/stop-child-benefit"

    def formula(benunit, period, parameters):
        entitlement = benunit("child_benefit_entitlement", period)
        opts_out = benunit("child_benefit_opts_out", period)
        hitc = parameters(period).gov.hmrc.income_tax.charges.CB_HITC
        income = benunit.max(benunit.members("adjusted_net_income", period))
        # Compute the fraction independently of payment to avoid the cycle
        # child_benefit -> CB_HITC -> child_benefit.
        charge_fraction = child_benefit_charge_share(
            income, hitc.phase_out_start, hitc.phase_out_end
        )
        opt_out_share = parameters(period).gov.hmrc.child_benefit.opt_out_charge_share
        remains_opted_out = (charge_fraction > 0) & (charge_fraction >= opt_out_share)
        charge = benunit.simulation.tax_benefit_system.get_variable("CB_HITC")
        if charge.is_neutralized:
            remains_opted_out = False
        return entitlement * ~(opts_out & remains_opted_out)
