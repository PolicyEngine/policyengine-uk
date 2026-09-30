from policyengine_uk.model_api import *


class uc_minimum_income_floor_gross(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit minimum income floor individual threshold (gross)"
    documentation = (
        "The person's individual threshold before the deductions for income "
        "tax and National Insurance: the National Minimum Wage hourly rate "
        "for their age times their expected hours of work each week, "
        "converted to a monthly amount in whole pounds, over a year."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 90(2)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/90",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 88",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/88",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 6(1A)(a)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/6",
        ),
    ]

    def formula(person, period, parameters):
        expected_hours = parameters(
            period
        ).gov.dwp.universal_credit.work_requirements.default_expected_hours
        hourly_rate = person("minimum_wage", period).astype(np.float64)
        # Reg. 90(2) converts the weekly amount "to a monthly amount by
        # multiplying by 52 and dividing by 12", and reg. 6(1A)(a)
        # disregards any fraction of a pound in a reg. 90 threshold (ADM
        # H4079: 234.50 x 52 / 12 = 1,016). Rounding to a millionth first
        # keeps a whole-pound result whole in floating point.
        monthly = np.floor(
            np.round(hourly_rate * expected_hours * WEEKS_IN_YEAR / MONTHS_IN_YEAR, 6)
        )
        return monthly * MONTHS_IN_YEAR
