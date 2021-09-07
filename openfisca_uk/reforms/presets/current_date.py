from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *
from datetime import datetime
from openfisca_uk import CountryTaxBenefitSystem

DATE = datetime.now()
YEAR, MONTH, DAY = DATE.year, DATE.month, DATE.day
CURRENT_INSTANT = DATE.strftime("%Y-%m-%d")


def use_current_parameters(date: str = CURRENT_INSTANT) -> Reform:
    def modify_parameters(parameters: ParameterNode):
        for child in parameters.get_descendants():
            if isinstance(child, Parameter):
                current_value = child(date)
                child.update(period=f"year:{YEAR}:1", value=current_value)
        return parameters

    class reform(Reform):
        def apply(self):
            self.modify_parameters(modify_parameters)

    return reform
