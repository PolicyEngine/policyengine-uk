from policyengine_uk.model_api import *


class uc_has_deduction(Variable):
    label = "UC household has deductions"
    documentation = (
        "Whether this benefit unit has money deducted from its Universal "
        "Credit award to repay debts (advances, government debt or third "
        "party deductions). Assigned from the DWP-published incidence of "
        "deductions among UC households, adjusted by region, to a unit "
        "claiming UC with an award left after the benefit cap. A protected "
        "floor reform limits what the cap and deductions together take to "
        "the floor allowance, so a family the cap takes to nil under current "
        "law can keep an award there. A "
        "latent deduction rate counts only where this is true, including a "
        "rate a dataset or situation supplies: to give a household situation "
        "deductions, set this to true with the rate. Explicitly supplied "
        "advance amounts and deduction rates apply whatever this says."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        # Estimation fallback: datasets can impute this directly (or override
        # the draw); the parameters live under gov.simulation because they
        # describe the world, not the law.
        p = parameters(period).gov.simulation.uc_deductions
        d = p.latent_rate_distribution
        incidence = (
            d.UNDER_5
            + d.AT_5
            + d.FIVE_TO_10
            + d.AT_10
            + d.TEN_TO_15
            + d.AT_15
            + d.FIFTEEN_TO_20
            + d.AT_20
            + d.TWENTY_TO_25
            + d.AT_25
            + d.OVER_25
        )
        region = benunit.household("region", period)
        adjusted_incidence = clip(incidence * p.region_incidence_factor[region], 0, 1)
        # The award deductions can come from: what the benefit cap leaves,
        # where a protected floor limits the cap to the floor allowance
        # (uc_maximum_reduction). Under current law the floor is zero, the
        # allowance infinite, and this is the award after the gross cap. A
        # family the gross cap takes to nil keeps an award under a binding
        # floor, and allocate_uc_reductions meets deductions from it first.
        cap_reduction = min_(
            benunit("uc_benefit_cap_reduction", period),
            benunit("uc_maximum_reduction", period),
        )
        award = max_(
            benunit("universal_credit_pre_benefit_cap", period) - cap_reduction,
            0,
        )
        on_uc = (
            benunit("claims_universal_credit", period)
            & (award > 0)
            & benunit("uc_award_carries_deductions", period)
        )
        draw = benunit("uc_deduction_random_draw", period)
        return on_uc & (draw < adjusted_incidence)
