from policyengine_uk.model_api import *
from policyengine_uk.utils.pence import stored_pence


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
        "claimant. Net earnings are whole pence, since carers_allowance_earnings "
        "applies regulation 5 to each step, and the test reads back the whole "
        "pence exactly, although the model stores amounts in single precision, "
        "which holds most sums of money only to within a fraction of a penny."
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
    ]

    def formula(person, period, parameters):
        limit = parameters(period).gov.dwp.carers_allowance.earnings_limit
        earnings = person("carers_allowance_earnings", period)
        # carers_allowance_earnings is whole pence, which float32 holds to
        # within half a step (£10,608.52 as 10,608.51953125); stored_pence
        # recovers them exactly below £131,072 a year. An amount entered
        # directly with a fraction of a penny has the fraction disregarded
        # (reg. 5).
        annual_pence = np.floor(stored_pence(earnings))
        # Spread over 52 weeks (reg. 8(1)(b)(iii)), disregarding the fraction
        # of a penny that leaves (reg. 5). Both steps are exact in float64, so
        # no floating-point rounding decides whether earnings have exceeded
        # the limit (ICA Regulations reg. 8(1)).
        weekly_pence = np.floor(annual_pence / WEEKS_IN_YEAR)
        # Rounding to a millionth of a penny keeps a limit such as £204.10
        # from being read as 20,409.999... pence.
        return weekly_pence > np.round(limit * 100, 6)
