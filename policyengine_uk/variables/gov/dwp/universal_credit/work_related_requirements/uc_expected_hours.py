from policyengine_uk.model_api import *


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
        p = parameters(period)
        hours = p.gov.dwp.universal_credit.work_requirements
        carer_hours = hours.responsible_carer.expected_hours
        youngest = person.benunit("uc_youngest_child_age", period)
        lesser = where(
            p.gov.dfe.compulsory_school_age.calc(youngest),
            # Reg. 88(2)(b): a child of compulsory school age under 13.
            carer_hours.compulsory_school_age,
            # Reg. 88(2)(aa): a child below compulsory school age.
            carer_hours.below_compulsory_school_age,
        )
        applies = person("uc_is_responsible_carer", period) & (
            youngest < carer_hours.child_age_limit
        )
        # Reg. 88(1): 35 "unless some lesser number of hours applies".
        return where(
            applies,
            min_(lesser, hours.default_expected_hours),
            hours.default_expected_hours,
        )
