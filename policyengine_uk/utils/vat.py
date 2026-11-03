from pathlib import Path

import numpy as np
import yaml

_LEGACY_PATH = (
    Path(__file__).parents[1]
    / "parameters"
    / "gov"
    / "simulation"
    / "microdata_vat_coverage.yaml"
)
# The declared value of the deprecated combined factor. A reform that moves the
# parameter away from it is honoured; otherwise the two factors are used.
LEGACY_COVERAGE_DEFAULT = float(
    list(yaml.safe_load(_LEGACY_PATH.read_text())["values"].values())[-1]
)


def vat_grossing_factor(simulation_parameters):
    """Factor that household VAT on recorded consumption is divided by.

    The product of survey consumption coverage and the household share of VAT
    liabilities, unless a reform has set the deprecated combined parameter
    `microdata_vat_coverage` to another value, in which case that value is used
    so that existing reforms keep working.
    """
    legacy = simulation_parameters.microdata_vat_coverage
    if not np.isclose(legacy, LEGACY_COVERAGE_DEFAULT):
        return legacy
    return (
        simulation_parameters.vat.survey_consumption_coverage
        * simulation_parameters.vat.household_share_of_receipts
    )
