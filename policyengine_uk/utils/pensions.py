import numpy as np


def pension_contributions_relief_amount(
    contributions, relevant_uk_earnings, ras_contributions, age, hmrc
):
    """FA 2004 ss. 188–191 relief for the supplied actual pay/contributions.

    Only RAS can use the basic-amount increase above earnings (s. 191(7)).
    The annual allowance does not cap relief, and payments from age 75 are
    unrelievable. Keeping this calculation shared lets the AA income tests
    exclude the NICs-only salary-sacrifice reclassification exactly.
    """
    basic_amount_increase = np.minimum(
        np.maximum(
            0,
            hmrc.income_tax.reliefs.pension_contribution.basic_amount
            - relevant_uk_earnings,
        ),
        ras_contributions,
    )
    annual_limit = relevant_uk_earnings + basic_amount_increase
    under_age_limit = age < hmrc.pensions.pension_contributions_relief_age_limit
    return np.minimum(contributions, annual_limit) * under_age_limit
