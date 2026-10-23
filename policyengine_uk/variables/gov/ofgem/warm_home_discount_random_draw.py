from policyengine_uk.model_api import *
from policyengine_uk.utils.stochastic import splitmix64_uniform


class warm_home_discount_random_draw(Variable):
    label = "Warm Home Discount receipt random draw"
    documentation = (
        "Uniform draw on [0, 1) that decides whether a household receiving a "
        "qualifying benefit also receives the Warm Home Discount rebate. "
        "Deterministic hash of the household id in dataset simulations; 0 in "
        "single-household simulations, so a qualifying household receives the "
        "rebate unless this is set. Datasets and situations can override it."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    default_value = 0.0

    def formula(household, period, parameters):
        # Representative microdata carries tens of millions of households of
        # weight; single-household situations carry ~1. Only assign hashed
        # draws in representative simulations: the 0 default is below any
        # receipt rate, so calculators show the rebate unless set.
        if household("household_weight", period).sum() < 1e6:
            return np.zeros(household.count)
        ids = household("household_id", period)
        return splitmix64_uniform(ids, salt=2)
