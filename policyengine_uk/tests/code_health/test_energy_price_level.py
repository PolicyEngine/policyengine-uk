"""Energy inputs must stay outside unconditional dataset uprating.

Unlabelled files retain flat energy spending: their data year does not
establish their price year. An explicit energy_price_basis instead opts into
the conditional annual CPI projector (#2526). A YAML entry would grow the
unlabelled files and could grow a declared observation twice.

This guard covers the unconditional YAML map. Core still uses the variables'
class-level uprating for direct situation inputs; that separate behavior is
preserved and tested in test_energy_dataset_projection.py.
"""

from pathlib import Path

import yaml

UPRATING_INDICES = Path(__file__).parents[2] / "data" / "uprating_indices.yaml"

# Projection is conditional on the observation's explicit price declaration.
ENERGY_VARIABLES_AT_BUILD_PRICE_LEVEL = {
    "domestic_energy_consumption",
    "electricity_consumption",
    "gas_consumption",
}


def test_energy_variables_are_not_projected_by_any_index():
    listed = yaml.safe_load(UPRATING_INDICES.read_text())
    offenders = sorted(
        f"{variable} (under {index})"
        for index, variables in listed.items()
        for variable in variables
        if variable in ENERGY_VARIABLES_AT_BUILD_PRICE_LEVEL
    )
    assert not offenders, (
        "these variables must use the conditional energy_price_basis "
        f"projector, not an unconditional YAML index: {offenders}. See #2526."
    )
