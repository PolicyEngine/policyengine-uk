from policyengine_uk.model_api import *


class child_benefit(Variable):
    label = "Child Benefit"
    documentation = "Total Child Benefit for the benefit unit"
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
        # child_benefit -> CB_HITC -> child_benefit. An infinite phase-out
        # endpoint also reduces the charge fraction to zero.
        charge_fraction = max_(income - hitc.phase_out_start, 0) / (
            hitc.phase_out_end - hitc.phase_out_start
        )
        charge_applies = charge_fraction > 0
        # The dataset flag describes a charge-driven decision. A reform that
        # removes the charge restores payments without changing entitlement.
        charge = benunit.simulation.tax_benefit_system.get_variable("CB_HITC")
        if charge.is_neutralized:
            charge_applies = False
        return entitlement * ~(opts_out & charge_applies)
