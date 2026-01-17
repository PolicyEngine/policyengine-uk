from .cps import create_marriage_tax_reform
from .conservatives import create_household_based_hitc_reform
from .policyengine import (
    disable_simulated_benefits,
)
from .policyengine.adjust_budgets import adjust_budgets
from .policyengine.abolish_council_tax import (
    create_abolish_council_tax_reform,
)
from .policyengine.two_child_limit_age_exemption import (
    create_two_child_limit_age_exemption_reform,
)
from .policyengine.freeze_pension_credit import (
    create_freeze_pension_credit_reform,
)
from .policyengine.employer_ni_pension_exemption import (
    create_employer_ni_pension_exemption_reform,
)
from .policyengine.salary_sacrifice_haircut import (
    create_salary_sacrifice_haircut_reform,
)
from .scotland import create_scottish_child_payment_reform
from .ubi_center import create_basic_income_interactions_reform
from policyengine_core.model_api import *
from policyengine_core import periods


def create_structural_reforms_from_parameters(parameters, period):
    period = periods.period(period)
    reforms = [
        create_marriage_tax_reform(parameters, period),
        create_household_based_hitc_reform(parameters, period),
        disable_simulated_benefits(parameters, period),
        adjust_budgets(parameters, period),
        create_abolish_council_tax_reform(parameters, period),
        create_scottish_child_payment_reform(parameters, period),
        create_two_child_limit_age_exemption_reform(parameters, period),
        create_freeze_pension_credit_reform(parameters, period),
        create_employer_ni_pension_exemption_reform(parameters, period),
        create_salary_sacrifice_haircut_reform(parameters, period),
        create_basic_income_interactions_reform(parameters, period),
    ]
    reforms = tuple(filter(lambda x: x is not None, reforms))

    class combined_reform(Reform):
        def apply(self):
            for reform in reforms:
                reform.apply(self)

    return combined_reform
