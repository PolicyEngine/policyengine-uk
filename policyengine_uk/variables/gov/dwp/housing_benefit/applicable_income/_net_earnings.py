from policyengine_uk.model_api import *


def person_net_earnings(
    person,
    period,
    pension_contribution_deduction_rate,
    statutory_pay_is_earnings=True,
):
    """A person's net earnings under the legacy means tests' earnings rules.

    HB Regs 2006 reg 35(1) includes "any remuneration or profit derived from
    that employment"; reg 35(1)(i) expressly includes statutory sick, maternity
    and paternity pay. The model's employee earnings components are
    employment_income and employment_benefits (SSP, SMP and SPP). Retaining
    that statutory-pay aggregate also retains simulation and reform overrides.
    Reg 35(2) excludes occupational pensions and expenses wholly, exclusively
    and necessarily incurred in the employment. The self_employment_income
    component is profit under reg 38, with losses
    prevented from offsetting another employment's earnings by reg 38(10).

    Reg 36(3) deducts "income tax", "primary Class 1 contributions" and
    "one-half" of occupational and personal pension contributions. Pension-age
    HB Regs 2006 reg 35(1)(h)-(i) and reg 36(2) apply the same rules to the
    statutory pay represented here. Class 2 and 4 contributions are deducted
    from self-employment profit under reg 38. Each scheme passes its own
    pension-contribution deduction rate.

    Income Support passes statutory_pay_is_earnings=False: IS Regs 1987 reg
    35(2)(b) excludes remuneration paid while the claimant is on maternity,
    paternity or other parental leave or absent from work because ill, and
    reg 40(4)(a) counts it as income other than earnings. Earnings are then
    employment income and self-employment profit only, and the primary Class 1
    contributions deducted are those on the wages: Class 1 is levied on wages
    and statutory pay together (ni_class_1_income), so it is attributed to the
    wages by their share of that base, as income tax is attributed below.

    The existing tax-attribution approximation uses earnings' share of an
    explicit raw income base including statutory pay, before losses, and tax
    before the Winter Fuel Payment charge. This is independent of the income
    tax definition of total_income and its component list. Housing Benefit
    (housing_benefit_net_earnings), Council Tax Reduction
    (council_tax_reduction_net_earnings) and Income Support
    (income_support_net_earnings) use these deductions.
    """
    employment_income = person("employment_income", period)
    self_employment_income = person("self_employment_income", period)
    # HB Regs 2006 reg 35(1)(i); pension age reg 35(1)(h)-(i):
    # employment_benefits contains statutory sick, maternity and paternity pay.
    statutory_pay = person("employment_benefits", period)
    earnings = max_(employment_income, 0) + max_(self_employment_income, 0)
    if statutory_pay_is_earnings:
        earnings = earnings + statutory_pay
    # Preserve the existing raw-income tax attribution independently of the
    # income tax definition of total_income. Floor each raw component before
    # summing, so that a loss cannot drop or inflate earnings' share of tax.
    # Occupational pensions and investment income belong only in this tax
    # denominator, not in the earnings defined by regs 35 and 38. Statutory
    # pay is in the denominator either way: it is taxed with wages.
    income_before_losses = statutory_pay + sum(
        max_(person(component, period), 0)
        for component in [
            "employment_income",
            "private_pension_income",
            "social_security_income",
            "self_employment_income",
            "property_income",
            "savings_interest_income",
            "other_investment_income",
            "dividend_income",
            "taxable_miscellaneous_income",
        ]
    )
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
    if statutory_pay_is_earnings:
        national_insurance = add(
            person, period, ["ni_class_1_employee", "ni_class_2", "ni_class_4"]
        )
    else:
        # Class 1 on the wages alone: the contributions times the share of
        # the Class 1 base that is not statutory pay, between nil and one.
        class_1_income = person("ni_class_1_income", period)
        statutory_pay_share = np.divide(
            statutory_pay,
            class_1_income,
            out=np.ones_like(class_1_income),
            where=class_1_income > 0,
        )
        class_1 = add(person, period, ["ni_class_1_employee"]) * max_(
            1 - statutory_pay_share, 0
        )
        national_insurance = class_1 + add(person, period, ["ni_class_2", "ni_class_4"])
    pension_contributions = (
        person("pension_contributions", period) * pension_contribution_deduction_rate
    )
    return max_(
        earnings - income_tax - national_insurance - pension_contributions,
        0,
    )
