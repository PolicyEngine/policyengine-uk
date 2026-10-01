from policyengine_uk.model_api import *


class uc_minimum_income_floor_gross(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit minimum income floor individual threshold (gross)"
    documentation = (
        "The person's individual threshold before the deductions for income "
        "tax and National Insurance: the National Minimum Wage hourly rate "
        "for their age (never the apprenticeship rate) times their expected "
        "hours of work each week, over a year."
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
            title="National Minimum Wage Regulations 2015 regs. 4 and 4A",
            href="https://www.legislation.gov.uk/uksi/2015/621/regulation/4A",
        ),
    ]

    def formula(person, period, parameters):
        p = parameters(period)
        expected_hours = (
            p.gov.dwp.universal_credit.work_requirements.default_expected_hours
        )
        # Reg. 90(2) uses the rate "a person of the same age as the claimant
        # would be paid" under NMW Regs reg. 4 or 4A(1)(a) to (c): the rate
        # for their age, never the apprenticeship rate of reg. 4A(1)(d).
        hourly_rate = p.gov.hmrc.minimum_wage.non_apprentice.calc(person("age", period))
        # Reg. 6(1A)(a) disregards fractions of a pound only in amounts
        # calculated for reg. 90 itself. Floors DWP has issued keep the pence:
        # 1,642.72 a month for 2025-26 from a threshold of 1,851.85 (12.21 x
        # 35 x 52 / 12; University of Bath IPR, "Going it alone", 2025,
        # "information supplied by the DWP"), where a whole-pound threshold
        # would give 1,642.09. So the threshold here is not rounded.
        return hourly_rate * expected_hours * WEEKS_IN_YEAR
