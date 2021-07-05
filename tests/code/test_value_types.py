from openfisca_uk import BASELINE_VARIABLES
from openfisca_core.model_api import Enum


def test_variable_names_match_return_types():
    for var_name in BASELINE_VARIABLES:
        variable = BASELINE_VARIABLES[var_name]
        if var_name[:4] == "num_":
            assert variable.value_type == int
        elif var_name[:3] == "is_":
            assert variable.value_type == bool
        else:
            assert variable.value_type in (Enum, float, bool)
