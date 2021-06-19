# -*- coding: utf-8 -*-

import os
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_uk import entities
from openfisca_uk.microdata.simulation import Microsimulation
from openfisca_uk.tools.simulation import IndividualSim, PopulationSim
from openfisca_uk.reforms.presets.modelling import (
    reported_tax,
    reported_benefits,
    reported,
)

COUNTRY_DIR = os.path.dirname(os.path.abspath(__file__))

# Our country tax and benefit class inherits from the general TaxBenefitSystem class.
# The name CountryTaxBenefitSystem must not be changed, as all tools of the OpenFisca ecosystem expect a CountryTaxBenefitSystem class to be exposed in the __init__ module of a country package.
class CountryTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self):
        # We initialize our tax and benefit system with the general constructor
        super(CountryTaxBenefitSystem, self).__init__(entities.entities)

        # We add to our tax and benefit system all the variables
        self.add_variables_from_directory(
            os.path.join(COUNTRY_DIR, "variables")
        )

        # We add to our tax and benefit system all the legislation parameters defined in the  parameters files
        param_path = os.path.join(COUNTRY_DIR, "parameters")
        self.load_parameters(param_path)

        # We define which variable, parameter and simulation example will be used in the OpenAPI specification
        self.open_api_config = {
            "variable_example": "JSA",
            "parameter_example": "taxes.income_tax.income_tax",
            "simulation_example": None,
        }


BASELINE_PARAMETERS = CountryTaxBenefitSystem().parameters


class AttributeDict(dict):
    __slots__ = ()
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


BASELINE_VARIABLES = AttributeDict(
    {
        name: value.__class__
        for name, value in CountryTaxBenefitSystem().variables.items()
    }
)
