from policyengine_uk import BASELINE_VARIABLES
from policyengine_core.model_api import Enum


def test_variable_names_match_return_types():
    exceptions = []
    for var_name in BASELINE_VARIABLES:
        variable = BASELINE_VARIABLES[var_name]
        try:
            if var_name[:4] == "num_":
                assert variable.value_type == int
            elif var_name[:3] == "is_":
                assert variable.value_type == bool
            else:
                assert variable.value_type in (Enum, float, bool, str, int)
        except Exception as e:
            exceptions += [f"{var_name} returns {variable.value_type}"]
    print(
        f"Total variables: {len(BASELINE_VARIABLES)}, variable name violations: {len(exceptions)}."
    )
    for exception in exceptions:
        print(f"\t{exception}")
    if len(exceptions) > 0:
        raise Exception("Some variable names do not match their output types.")


def test_labels_exist():
    messages = []
    for var_name in BASELINE_VARIABLES:
        if not hasattr(BASELINE_VARIABLES[var_name], "label"):
            messages += [f"{var_name} has no label set"]
        elif BASELINE_VARIABLES[var_name].label == "label":
            messages += [f"{var_name} has the default label"]
    if len(messages) > 0:
        print("\n".join(messages))
        raise Exception("Some variables do not have labels.")
