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
        "claimant. Annual earnings are first taken to the nearest penny, "
        "because the model stores them in single precision, which holds most "
        "sums of money only to within a fraction of a penny."
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
    ]

    def formula(person, period, parameters):
        limit = parameters(period).gov.dwp.carers_allowance.earnings_limit
        earnings = person("carers_allowance_earnings", period)
        # Earnings are a sum of money, a whole number of pence, but the model
        # stores them in float32, which holds most such sums only to within a
        # fraction of a penny: £10,608.52 is stored as 10,608.51953125. Take
        # the nearest penny, in float64, to recover the sum, with an exact
        # half penny disregarded (reg. 5). Then count the weekly pence
        # exactly, disregarding the fraction of a penny that spreading over
        # 52 weeks leaves (reg. 5), so that no floating-point rounding
        # decides whether earnings exceed the limit (reg. 8(1)).
        annual_pence = np.ceil(earnings.astype(np.float64) * 100 - 0.5)
        weekly_pence = annual_pence // WEEKS_IN_YEAR
        # Rounding to a millionth of a penny keeps a limit such as £204.10
        # from being read as 20,409.999... pence.
        return weekly_pence > np.round(limit * 100, 6)
