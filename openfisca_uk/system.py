# -*- coding: utf-8 -*-

import os
from openfisca_uk import entities
import os
from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_uk.parameters.gov.ofgem.price_cap.add_price_cap_parameters import (
    add_price_cap_parameters,
)
from openfisca_tools.parameters import uprate_parameters

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
        self.parameters = add_price_cap_parameters(
            self.parameters,
            start_year=2019,
            start_quarter=1,
            end_year=2027,
            end_quarter=4,
        )

        self.parameters = uprate_parameters(self.parameters)

        self.parameters.add_child("baseline", self.parameters.clone())

        # We define which variable, parameter and simulation example will be used in the OpenAPI specification
        self.open_api_config = {
            "variable_example": "JSA",
            "parameter_example": "taxes.income_tax.income_tax",
            "simulation_example": None,
        }
