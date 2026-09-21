"""Energy variables must not be CPI-uprated.

policyengine-uk-data calibrates the energy variables to NEED mean kWh and
converts to pounds at Ofgem Q2 2026 unit rates, so the stored values already
carry FY26/27 price levels. Its imputations/consumption.py states that they
"are not CPI-uprated, so this avoids the need for price-level adjustment at
simulation time".

Uprating them from the dataset's data year re-applies price changes the build
has already applied. #1859 reported the resulting inconsistency and #1860
resolved it the wrong way round — by uprating electricity and gas to match
domestic_energy_consumption, rather than by removing all three (#1867).

This guard stops that from happening again.
"""

from pathlib import Path

import yaml

UPRATING_INDICES = Path(__file__).parents[2] / "data" / "uprating_indices.yaml"

# Calibrated to NEED at Ofgem Q2 2026 rates, so already at FY26/27 prices.
ENERGY_VARIABLES_AT_BUILD_PRICE_LEVEL = {
    "domestic_energy_consumption",
    "electricity_consumption",
    "gas_consumption",
}


def test_energy_variables_are_not_uprated_by_any_index():
    listed = yaml.safe_load(UPRATING_INDICES.read_text())
    offenders = sorted(
        f"{variable} (under {index})"
        for index, variables in listed.items()
        for variable in variables
        if variable in ENERGY_VARIABLES_AT_BUILD_PRICE_LEVEL
    )
    assert not offenders, (
        "these variables are stored at the data build's own FY26/27 price "
        f"level and must not be uprated: {offenders}. See #1867."
    )
