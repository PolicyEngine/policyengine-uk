# -*- coding: utf-8 -*-

import os
from openfisca_uk import entities
import os
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_tools.parameters import (
    interpolate_parameters,
    uprate_parameters,
)

COUNTRY_DIR = os.path.dirname(os.path.abspath(__file__))


class CountryTaxBenefitSystem(TaxBenefitSystem):
    CURRENCY = "£"

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

        self.parameters = interpolate_parameters(self.parameters)
        self.parameters = uprate_parameters(self.parameters)
        self.parameters.baseline = self.parameters.clone()

        # We define which variable, parameter and simulation example will be used in the OpenAPI specification
        self.open_api_config = {
            "variable_example": "JSA",
            "parameter_example": "taxes.income_tax.income_tax",
            "simulation_example": None,
        }
