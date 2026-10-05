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
        charge_applies = income > hitc.phase_out_start
        # The dataset flag describes a charge-driven decision. A reform that
        # removes the charge restores payments without changing entitlement.
        charge = benunit.simulation.tax_benefit_system.get_variable("CB_HITC")
        if charge.is_neutralized:
            charge_applies = False
        return entitlement * ~(opts_out & charge_applies)
