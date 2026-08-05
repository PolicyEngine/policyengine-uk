from policyengine_uk.model_api import *
from policyengine_uk.utils.stochastic import splitmix64_uniform


class uc_deduction_random_draw(Variable):
    label = "UC deduction random draw"
    documentation = (
        "Uniform draw on [0, 1) determining deduction incidence and size. "
        "Deterministic hash of the benefit unit id in dataset simulations; "
        "0.5 in single-household simulations (no deduction unless set). "
        "Datasets and situations can override it directly."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    default_value = 0.5

    def formula(benunit, period, parameters):
        # Representative microdata carries tens of millions of households of
        # weight; single-household situations carry ~1. Only assign hashed
        # draws in representative simulations.
        if benunit("benunit_weight", period).sum() < 1e6:
            return np.ones(benunit.count) * 0.5
        ids = benunit("benunit_id", period)
        return splitmix64_uniform(ids, salt=0)
