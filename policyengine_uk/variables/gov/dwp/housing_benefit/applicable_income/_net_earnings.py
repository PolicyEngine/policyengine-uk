from policyengine_uk.model_api import *


def person_net_earnings(person, period, pension_contribution_deduction_rate):
    """A person's net earnings under the legacy means tests' earnings rules.

    Employment income plus self-employment profit (each floored at zero) plus
    statutory sick and maternity pay, less the income tax attributed to them
    (before the winter fuel payment charge),
    Class 1, 2 and 4 National Insurance and the scheme's share of pension
    contributions, floored at zero. Housing Benefit
    (housing_benefit_net_earnings) and the Council Tax Reduction pensioner
    earnings disregards (council_tax_reduction_net_earnings) use these
    deductions. Each scheme's regulations state their own share of pension
    contributions, so each passes its own rate.
    """
    employment_income = person("employment_income", period)
    self_employment_income = person("self_employment_income", period)
    # Statutory sick and maternity pay are earnings (HB Regs 2006 reg
    # 35(1)(i); pension age reg 35(1)(h)). The model taxes them as employment income
    # (employment_benefits) but leaves them out of total_income.
    statutory_pay = person("employment_benefits", period)
    earnings = (
        max_(employment_income, 0) + max_(self_employment_income, 0) + statutory_pay
    )
    # Income tax is attributed by the earnings' share of total income,
    # with statutory pay added and before any negative component (a
    # loss), so that a loss set against other income does not drop or
    # inflate the share of tax on these earnings.
    income_before_losses = person("total_income", period) + statutory_pay
    system = person.simulation.tax_benefit_system
    for component in system.get_variable("total_income").adds:
        income_before_losses += max_(-person(component, period), 0)
    earnings_share = np.divide(
        earnings,
        income_before_losses,
        out=np.zeros_like(earnings),
        where=income_before_losses > 0,
    )
    # Tax before the winter fuel payment charge: the charge recovers a
    # payment and is not deducted from earnings.
    tax = person("income_tax_before_winter_fuel_payment_charge", period)
    income_tax = tax * min_(earnings_share, 1)
    national_insurance = add(
        person, period, ["ni_class_1_employee", "ni_class_2", "ni_class_4"]
    )
    pension_contributions = (
        person("pension_contributions", period) * pension_contribution_deduction_rate
    )
    return max_(
        earnings - income_tax - national_insurance - pension_contributions,
        0,
    )
