# -*- coding: utf-8 -*-

import os
from policyengine_uk import entities
from policyengine_uk.system import (
    CountryTaxBenefitSystem,
    Microsimulation,
    Simulation,
    COUNTRY_DIR,
    parameters,
    variables,
)
from pathlib import Path
import os
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_uk.data.economic_assumptions import (
    BASELINE_GROWFACTORS,
    apply_growth_factors,
)

REPO = Path(__file__).parent
