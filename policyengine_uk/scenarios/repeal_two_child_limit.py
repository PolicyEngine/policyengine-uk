import numpy as np

from policyengine_uk.model_api import Scenario

repeal_two_child_limit = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.elements.child.limit.child_count": {
            "year:2026:10": np.inf
        }
    }
)
