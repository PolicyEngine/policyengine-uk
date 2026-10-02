from policyengine_uk.model_api import *

STATUTORY_PAY = [
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
]


def working_age_earnings_components(person, period):
    """Gross earnings, employed earnings, pension deduction and tax per person.

    With an award of Universal Credit, earnings follow the Universal Credit
    measure (with any minimum income floor) and all pension contributions are
    deducted; otherwise employment and self-employment income count and half
    of pension contributions are deducted. Statutory sick, maternity and
    paternity pay are employed earnings on both routes (SSI 2021/249 regs
    49(4), 50(2); WSI 2013/3029 Sch 6 para 14(1)).
    """
    has_universal_credit = person.benunit(
        "council_tax_reduction_working_age_has_universal_credit", period
    )
    statutory_pay = add(person, period, STATUTORY_PAY)
    employment = person("employment_income", period)
    universal_credit_gross = (
        person("uc_mif_capped_earned_income", period) + statutory_pay
    )
    legacy_gross = employment + person("self_employment_income", period) + statutory_pay
    gross = where(has_universal_credit, universal_credit_gross, legacy_gross)
    employed_gross = min_(employment + statutory_pay, gross)
    pension_share = where(has_universal_credit, 1, 0.5)
    pension_deduction = person("pension_contributions", period) * pension_share
    tax = person("tax", period)
    return gross, employed_gross, pension_deduction, tax
