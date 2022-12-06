# -*- coding: utf-8 -*-

import os
from policyengine_uk import entities
from policyengine_uk.system import (
    CountryTaxBenefitSystem,
    Microsimulation,
    Simulation,
    IndividualSim,
    COUNTRY_DIR,
    BASELINE_VARIABLES,
    parameters,
    variables,
)
from pathlib import Path
import os
from policyengine_core.taxbenefitsystems import TaxBenefitSystem

from policyengine_uk.data import (
    FRS,
    RawFRS,
    SPI,
    RawSPI,
    RawLCFS,
    RawWAS,
    ExtendedFRS,
    LCFS,
    WAS,
    CalibratedFRS,
    EnhancedFRS,
    SynthFRS,
)

REPO = Path(__file__).parent

DATASETS = [EnhancedFRS, SynthFRS, FRS, RawFRS]
