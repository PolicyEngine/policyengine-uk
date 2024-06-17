from .cps import create_marriage_tax_reform
from .conservatives import create_household_based_hitc_reform
from .policyengine import create_budget_change_reform
from policyengine_core.model_api import *
from policyengine_core import periods


def create_structural_reforms_from_parameters(parameters, period):
    period = periods.period(period)
    reforms = [
        create_marriage_tax_reform(parameters, period),
        create_household_based_hitc_reform(parameters, period),
        create_budget_change_reform(parameters, period),
    ]
    reforms = tuple(filter(lambda x: x is not None, reforms))

    class combined_reform(Reform):
        def apply(self):
            for reform in reforms:
                reform.apply(self)

    return combined_reform
