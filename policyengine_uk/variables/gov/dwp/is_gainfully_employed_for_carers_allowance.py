from policyengine_uk.model_api import *


class is_gainfully_employed_for_carers_allowance(Variable):
    value_type = bool
    entity = Person
    label = "gainfully employed for Carer's Allowance"
    documentation = (
        "Whether the person's weekly net earnings exceed the Carer's Allowance "
        "earnings limit, so that they are treated as gainfully employed and "
        "are not entitled to the allowance. The regulation tests the earnings "
        "of the preceding week; annual earnings are spread evenly over 52 "
        "weeks. A fraction of a penny is disregarded, as regulation 5 of the "
        "Computation of Earnings Regulations requires when that favours the "
        "claimant. Net earnings are whole pence less half of pension "
        "contributions, so the model first takes the annual figure to the "
        "nearest half penny, because it stores amounts in single precision, "
        "which holds most sums of money only to within a fraction of a penny. "
        "The half penny of an odd-pence pension contribution then counts as a "
        "penny off earnings, which favours the claimant."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s. 70(1)(b)",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        ),
        dict(
            title="The Social Security (Invalid Care Allowance) Regulations 1976 reg. 8(1)",
            href="https://www.legislation.gov.uk/uksi/1976/409/regulation/8",
        ),
        dict(
            title="Social Security Benefit (Computation of Earnings) Regulations 1996 reg. 5",
            href="https://www.legislation.gov.uk/uksi/1996/2745/regulation/5",
        ),
        dict(
            title="Social Security Benefit (Computation of Earnings) Regulations 1996 reg. 8(1)(b)(iii)",
            href="https://www.legislation.gov.uk/uksi/1996/2745/regulation/8",
        ),
        dict(
            title="Social Security Benefit (Computation of Earnings) Regulations 1996 reg. 10(4)(b)",
            href="https://www.legislation.gov.uk/uksi/1996/2745/regulation/10",
        ),
    ]

    def formula(person, period, parameters):
        limit = parameters(period).gov.dwp.carers_allowance.earnings_limit
        earnings = person("carers_allowance_earnings", period)
        # Net earnings are pay less tax and NI, in whole pence, less half of
        # pension contributions (reg. 10(4)(b)): a whole number of half pence.
        # The model stores them in float32, which holds most such sums only to
        # within a fraction of a penny (£10,608.52 is stored as
        # 10,608.51953125), so take the nearest half penny, in float64, to
        # recover the sum. Then disregard a half penny: counting the half
        # penny of the pension deduction as a penny favours the claimant
        # (reg. 5). Spread the pence over 52 weeks (reg. 8(1)(b)(iii)) and
        # disregard the fraction of a penny that leaves (reg. 5). Each step
        # is exact in float64 for every float32 amount, so no floating-point
        # rounding decides whether earnings have exceeded the limit (ICA
        # Regulations reg. 8(1)).
        annual_half_pence = np.ceil(earnings.astype(np.float64) * 200 - 0.5)
        annual_pence = np.floor(annual_half_pence / 2)
        weekly_pence = np.floor(annual_pence / WEEKS_IN_YEAR)
        # Rounding to a millionth of a penny keeps a limit such as £204.10
        # from being read as 20,409.999... pence.
        return weekly_pence > np.round(limit * 100, 6)
