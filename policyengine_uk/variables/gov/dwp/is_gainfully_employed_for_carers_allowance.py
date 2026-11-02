from policyengine_uk.model_api import *


class is_gainfully_employed_for_carers_allowance(Variable):
    value_type = bool
    entity = Person
    label = "gainfully employed for Carer's Allowance"
    documentation = (
        "Whether the person's weekly net earnings exceed the Carer's Allowance "
        "earnings limit, so that they are treated as gainfully employed and "
        "are not entitled to the allowance. The formula reads "
        "carers_allowance_weekly_earnings_above_limit, which spreads annual "
        "earnings over 52 weeks and compares them with the limit in whole "
        "pence, disregarding a fraction of a penny as regulation 5 of the "
        "Computation of Earnings Regulations requires when that favours the "
        "claimant. Any excess, however small, means the person is gainfully "
        "employed."
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
        # The excess is a whole number of pence of at least 1p wherever
        # earnings exceed the limit, which float32 holds as a positive
        # amount, and exactly zero otherwise.
        return person("carers_allowance_weekly_earnings_above_limit", period) > 0
