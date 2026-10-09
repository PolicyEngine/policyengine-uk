from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data
from policyengine_uk.utils.stochastic import splitmix64_uniform


class uc_deduction_type_random_draw(Variable):
    label = "UC deduction type random draw"
    documentation = (
        "Uniform draw on [0, 1) determining the deduction type combination. "
        "Deterministic hash of the benefit unit id in simulations built from "
        "data, including a region or constituency filtered from them; 1.0 in "
        "household situations. Datasets and situations can override it "
        "directly."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    default_value = 1.0

    def formula(benunit, period, parameters):
        # Hashed draws in every simulation built from data, however little
        # weight it carries. Household situations get 1.0, which maps to the
        # last type combination but only matters when a deduction is assigned.
        if not built_from_data(benunit.simulation):
            return np.ones(benunit.count)
        ids = benunit("benunit_id", period)
        return splitmix64_uniform(ids, salt=1)
