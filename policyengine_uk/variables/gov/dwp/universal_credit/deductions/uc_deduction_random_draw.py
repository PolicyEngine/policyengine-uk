from policyengine_uk.model_api import *
from policyengine_uk.utils.stochastic import splitmix64_uniform


class uc_deduction_random_draw(Variable):
    label = "UC deduction random draw"
    documentation = (
        "Uniform draw on [0, 1) determining deduction incidence and size. "
        "Deterministic hash of the benefit unit id in simulations built from "
        "data, including a region or constituency filtered from them; 1.0 in "
        "household situations, so no deduction unless set. Datasets and "
        "situations can override it directly."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    default_value = 1.0

    def formula(benunit, period, parameters):
        # Hashed draws in every simulation built from data, however little
        # weight it carries: a constituency filtered from the national data is
        # still data. Household situations get 1.0, which never falls below
        # any incidence, so calculators get no deductions unless set.
        if not getattr(benunit.simulation, "built_from_dataset", False):
            return np.ones(benunit.count)
        ids = benunit("benunit_id", period)
        return splitmix64_uniform(ids, salt=0)
