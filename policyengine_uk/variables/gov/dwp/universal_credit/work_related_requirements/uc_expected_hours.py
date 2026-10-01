from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import expected_hours


class uc_expected_hours(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit expected hours of work each week"
    documentation = (
        "The expected number of hours per week: 35 unless a lesser number "
        "applies. The regulation leaves each lesser number to the Secretary "
        "of State. The model uses the hours DWP says it uses for the "
        "responsible carer of a child under 13 (a maximum of 30 since 2025; "
        "before that 16 for a child aged 3 or 4 and 25 for a school-age "
        "child). It sets no lesser number for a parent who is not the "
        "responsible carer or for a claimant with a physical or mental "
        "impairment: supply this variable where one applies."
    )
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 88",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/88",
        ),
        dict(
            title="Written answer 129349, 28 April 2026",
            href="https://questions-statements.parliament.uk/written-questions/detail/2026-04-22/129349",
        ),
    ]
    definition_period = YEAR
    unit = "hour"

    def formula(person, period, parameters):
        return expected_hours(
            person, period, parameters, person("uc_is_responsible_carer", period)
        )
