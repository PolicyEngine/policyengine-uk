from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data
from policyengine_uk.utils.stochastic import splitmix64_uniform


class warm_home_discount_random_draw(Variable):
    label = "Warm Home Discount receipt random draw"
    documentation = (
        "Uniform draw on [0, 1) that decides whether a household receiving a "
        "qualifying benefit also receives the Warm Home Discount rebate. "
        "Deterministic hash of the household id in simulations built from "
        "data, including a region or constituency filtered from them; 0 in "
        "household situations, so a qualifying household receives the rebate "
        "unless this is set. Datasets and situations can override it."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    default_value = 0.0

    def formula(household, period, parameters):
        # Hashed draws in every simulation built from data, however little
        # weight it carries: a constituency filtered from the national data is
        # still data. Household situations get 0, which is below any receipt
        # rate, so calculators show the rebate unless the draw is set.
        if not built_from_data(household.simulation):
            return np.zeros(household.count)
        ids = household("household_id", period)
        return splitmix64_uniform(ids, salt=2)
