from policyengine_uk.model_api import *

# Band edges of the DWP deductions distribution (Table 2 of the deductions
# supplementary tables), as fractions of the standard allowance. Bands where
# the lower and upper edges are equal are point masses at institutional rates.
# The final band holds above-cap deductions (last resort and child
# maintenance categories); the DWP tables top-code it, so 30% is a modeling
# assumption for its upper edge.
BAND_LOWER = np.array([0.0, 0.05, 0.05, 0.10, 0.10, 0.15, 0.15, 0.20, 0.20, 0.25, 0.25])
BAND_UPPER = np.array(
    [0.05, 0.05, 0.10, 0.10, 0.15, 0.15, 0.20, 0.20, 0.25, 0.25, 0.30]
)


class uc_latent_deduction_rate(Variable):
    label = "UC latent deduction rate"
    documentation = (
        "Deduction demand as a fraction of the Universal Credit standard "
        "allowance, before applying the statutory cap. Assigned by inverting "
        "the DWP-published distribution of deduction rates observed under "
        "the 25% cap (March to May 2025), so the cap parameter reproduces "
        "observed post-cap distributions and reforms to the cap rescale "
        "coherently. Validated for 2024 and 2025; earlier years apply the "
        "same distribution under the higher caps then in force. Demand is "
        "held fixed as the cap moves, so cuts below the 15% cap overstate "
        "the constrained population while cap increases toward 25% stay "
        "inside the observed window."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float

    def formula(benunit, period, parameters):
        # Estimation fallback: datasets can impute this directly (or override
        # the draw); the parameters live under gov.simulation because they
        # describe the world, not the law.
        p = parameters(period).gov.simulation.uc_deductions
        d = p.latent_rate_distribution
        shares = np.array(
            [
                d.UNDER_5,
                d.AT_5,
                d.FIVE_TO_10,
                d.AT_10,
                d.TEN_TO_15,
                d.AT_15,
                d.FIFTEEN_TO_20,
                d.AT_20,
                d.TWENTY_TO_25,
                d.AT_25,
                d.OVER_25,
            ]
        )
        total_share = shares.sum()
        if total_share <= 0:
            return np.zeros(benunit.count)
        has_deduction = benunit("uc_has_deduction", period)
        draw = benunit("uc_deduction_random_draw", period)
        region = benunit.household("region", period)
        adjusted_incidence = clip(
            total_share * p.region_incidence_factor[region], 1e-9, 1
        )
        # Conditional on assignment (draw < adjusted incidence), the rescaled
        # draw is uniform on [0, 1): use it as the quantile of the rate
        # distribution.
        quantile = clip(draw / adjusted_incidence, 0, 1 - 1e-9)
        position = quantile * total_share
        cumulative = np.cumsum(shares)
        band = np.searchsorted(cumulative, position, side="right")
        band = clip(band, 0, len(shares) - 1)
        cumulative_before = cumulative[band] - shares[band]
        within = (position - cumulative_before) / np.maximum(shares[band], 1e-12)
        rate = BAND_LOWER[band] + (BAND_UPPER[band] - BAND_LOWER[band]) * within
        return where(has_deduction, rate, 0)
