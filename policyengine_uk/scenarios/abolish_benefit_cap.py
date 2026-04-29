import numpy as np

from policyengine_uk.model_api import Scenario

abolish_benefit_cap = Scenario(
    parameter_changes={
        "gov.dwp.benefit_cap.single.in_london": {"year:2026:10": np.inf},
        "gov.dwp.benefit_cap.single.outside_london": {"year:2026:10": np.inf},
        "gov.dwp.benefit_cap.non_single.in_london": {"year:2026:10": np.inf},
        "gov.dwp.benefit_cap.non_single.outside_london": {"year:2026:10": np.inf},
    }
)
