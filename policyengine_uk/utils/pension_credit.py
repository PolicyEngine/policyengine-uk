def employed_earnings_sources(parameters, period) -> list:
    """Employment income and the statutory payments that the State Pension
    Credit Regulations 2002 reg. 17A(2) make earnings of an employed earner.

    The Schedule VI earnings disregard and the income tax payable on earnings
    (pension_credit_earnings_income_tax) both read this one list.
    """
    guarantee_credit = parameters(period).gov.dwp.pension_credit.guarantee_credit
    return ["employment_income"] + list(guarantee_credit.statutory_payments)
