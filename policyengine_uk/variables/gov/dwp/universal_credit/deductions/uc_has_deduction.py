from policyengine_uk.model_api import *


class uc_has_deduction(Variable):
    label = "UC household has deductions"
    documentation = (
        "Whether this benefit unit has money deducted from its Universal "
        "Credit award to repay debts (advances, government debt or third "
        "party deductions). Assigned from the DWP-published incidence of "
        "deductions among UC households, adjusted by region."
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
        award = max_(
            benunit("universal_credit_pre_benefit_cap", period)
            - benunit("benefit_cap_reduction", period),
            0,
        )
        on_uc = benunit("would_claim_uc", period) & (award > 0)
        draw = benunit("uc_deduction_random_draw", period)
        return on_uc & (draw < adjusted_incidence)
