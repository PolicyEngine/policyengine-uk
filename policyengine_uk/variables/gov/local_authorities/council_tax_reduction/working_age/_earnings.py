from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_wales_scheme,
)

STATUTORY_PAY = [
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
]

# Taxable unearned income the working-age schemes count. Tax on it is the part
# of a person's non-savings income tax that is not tax on their earnings,
# shared pro rata with property income (which the schemes treat as capital).
COUNTED_TAXABLE_UNEARNED = [
    "state_pension",
    "private_pension_income",
    "carers_allowance",
    "carer_support_payment_pre_overlap",
    "esa_contrib",
    "jsa_contrib",
    "incapacity_benefit",
]


def working_age_earnings(person, period):
    """Net earnings and the employed part of them, per person.

    Tax and National Insurance come off earnings only as far as they are in
    respect of the employment or trade: the model's Universal Credit split of
    each person's income tax (earnings taken as the lowest slice of
    non-savings income) and their Class 1, 2 and 4 contributions, not
    voluntary Class 3 (SSI 2021/249 regs 49(6), 50(3); WSI 2013/3029 Sch 6
    paras 15(3), 16). With an award of Universal Credit:
    - Wales uses the Secretary of State's figure for the award, which is the
      model's Universal Credit earned income before the work allowance
      (Sch 6 para 9). It follows the Universal Credit model, which does not
      yet count statutory pay as earnings (UC Regs 2013 reg 55(4));
    - Scotland uses the Universal Credit measure plus statutory sick,
      maternity and paternity pay, which reg 49(4) treats as earnings.
    Without Universal Credit, employment and self-employment income and
    statutory pay count, less half of pension contributions.
    Returns (net earnings, net employed earnings).
    """
    has_universal_credit = person.benunit(
        "council_tax_reduction_working_age_has_universal_credit", period
    )
    wales = is_wales_scheme(person.household("country", period))
    statutory_pay = add(person, period, STATUTORY_PAY)
    employment = person("employment_income", period)
    self_employment = person("self_employment_income", period)
    tax_on_earnings = add(
        person,
        period,
        ["uc_income_tax_on_earnings", "uc_national_insurance_on_earnings"],
    )
    universal_credit_earnings = person("uc_individual_earned_income", period)
    scotland_universal_credit = universal_credit_earnings + statutory_pay
    legacy_gross = employment + self_employment + statutory_pay
    legacy = max_(
        0,
        legacy_gross - 0.5 * person("pension_contributions", period) - tax_on_earnings,
    )
    net = where(
        has_universal_credit,
        where(wales, universal_credit_earnings, scotland_universal_credit),
        legacy,
    )
    gross = where(has_universal_credit, net, legacy_gross)
    employed_gross = employment + statutory_pay
    employed_share = np.divide(
        min_(employed_gross, gross),
        gross,
        out=np.zeros_like(gross, dtype=float),
        where=gross > 0,
    )
    return net, net * employed_share


def working_age_unearned_income_tax(person, period):
    """Income tax on the person's counted taxable unearned income."""
    counted = add(person, period, COUNTED_TAXABLE_UNEARNED)
    property_income = max_(0, person("property_income", period))
    other_non_savings_tax = max_(
        0,
        person("earned_income_tax", period)
        - person("uc_income_tax_on_earnings", period),
    )
    share = np.divide(
        counted,
        counted + property_income,
        out=np.zeros_like(counted, dtype=float),
        where=(counted + property_income) > 0,
    )
    return other_non_savings_tax * share
