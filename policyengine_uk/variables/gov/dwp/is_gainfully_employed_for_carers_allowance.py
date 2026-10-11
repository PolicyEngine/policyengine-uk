from policyengine_uk.model_api import *


class is_gainfully_employed_for_carers_allowance(Variable):
    value_type = bool
    entity = Person
    label = "gainfully employed for Carer's Allowance"
    documentation = (
        "Whether the person's weekly net earnings exceed the Carer's Allowance "
        "earnings limit, so that they are treated as gainfully employed and "
        "are not entitled to the allowance. The regulation tests the earnings "
        "of the preceding week; annual earnings are spread evenly over the year."
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
    ]

    def formula(person, period, parameters):
        limit = parameters(period).gov.dwp.carers_allowance.earnings_limit
        weekly_earnings = person("carers_allowance_earnings", period) / WEEKS_IN_YEAR
        return weekly_earnings > limit
