# -*- coding: utf-8 -*-

import os

from openfisca_core.taxbenefitsystems import TaxBenefitSystem

from openfisca_country_template import entities
from openfisca_country_template.situation_examples import couple


COUNTRY_DIR = os.path.dirname(os.path.abspath(__file__))


# Our country tax and benefit class inherits from the general TaxBenefitSystem class.
# The name CountryTaxBenefitSystem must not be changed, as all tools of the OpenFisca ecosystem expect a CountryTaxBenefitSystem class to be exposed in the __init__ module of a country package.
class CountryTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self):
        # We initialize our tax and benefit system with the general constructor
        super(CountryTaxBenefitSystem, self).__init__(entities.entities)

        # We add to our tax and benefit system all the variables
        self.add_variables_from_directory(os.path.join(COUNTRY_DIR, 'variables'))

        # We add to our tax and benefit system all the legislation parameters defined in the  parameters files
        param_path = os.path.join(COUNTRY_DIR, 'parameters')
        self.load_parameters(param_path)

        # We define which variable, parameter and simulation example will be used in the OpenAPI specification
        self.open_api_config = {
            "variable_example": "disposable_income",
            "parameter_example": "taxes.income_tax_rate",
            "simulation_example": couple,
            }
