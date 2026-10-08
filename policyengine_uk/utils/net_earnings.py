"""The existing individual earnings/tax-attribution convention, with a rate
provided by the calling benefit rather than borrowed from another program.
"""

import numpy as np


def net_earnings(person, period, pension_deduction_rate):
    employment = person("employment_income", period)
    self_employment = person("self_employment_income", period)
    statutory_pay = person("employment_benefits", period)
    gross = np.maximum(employment, 0) + np.maximum(self_employment, 0) + statutory_pay
    income_before_losses = person("total_income", period) + statutory_pay
    system = person.simulation.tax_benefit_system
    for component in system.get_variable("total_income").adds:
        income_before_losses += np.maximum(-person(component, period), 0)
    share = np.divide(
        gross,
        income_before_losses,
        out=np.zeros_like(gross),
        where=income_before_losses > 0,
    )
    tax = person("income_tax", period) * np.minimum(share, 1)
    ni = sum(
        person(name, period)
        for name in ("ni_class_1_employee", "ni_class_2", "ni_class_4")
    )
    return np.maximum(
        gross
        - tax
        - ni
        - person("pension_contributions", period) * pension_deduction_rate,
        0,
    )
