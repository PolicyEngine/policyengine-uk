# -*- coding: utf-8 -*-

import os
from openfisca_uk import entities
from openfisca_uk.system import CountryTaxBenefitSystem
from openfisca_uk.tools.simulation import (
    IndividualSim,
    Microsimulation,
    prepare_parameters,
)
from openfisca_uk.reforms.presets.modelling import (
    reported_tax,
    reported_benefits,
    reported,
)
from pathlib import Path
import os
from openfisca_core.taxbenefitsystems import TaxBenefitSystem

COUNTRY_DIR = os.path.dirname(os.path.abspath(__file__))

system = prepare_parameters(CountryTaxBenefitSystem())
parameters = BASELINE_PARAMETERS = system.parameters


class AttributeDict(dict):
    __slots__ = ()
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


BASELINE_VARIABLES = AttributeDict(
    {name: value.__class__ for name, value in system.variables.items()}
)
variables = BASELINE_VARIABLES
REPO = Path(__file__).parent

# Our country tax and benefit class inherits from the general TaxBenefitSystem class.
# The name CountryTaxBenefitSystem must not be changed, as all tools of the OpenFisca ecosystem expect a CountryTaxBenefitSystem class to be exposed in the __init__ module of a country package.
