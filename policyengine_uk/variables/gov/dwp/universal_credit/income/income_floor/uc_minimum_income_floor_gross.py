from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    ALL_REQUIREMENTS,
    INTERVIEW_ONLY,
    NO_REQUIREMENTS,
    WORK_PREPARATION,
    gross_threshold,
    threshold_hours,
)


class uc_minimum_income_floor_gross(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit minimum income floor individual threshold (gross)"
    documentation = (
        "The person's individual threshold before the deductions for income "
        "tax and National Insurance: the National Minimum Wage hourly rate "
        "for their age (never the apprenticeship rate) times a number of "
        "hours each week, over a year. The hours are the person's expected "
        "hours where they would otherwise be subject to all work-related "
        "requirements, and 16 where they would otherwise be subject to the "
        "work-focused interview requirement only or the work preparation "
        "requirement. The regulations set no threshold for a claimant "
        "subject to no work-related requirements for a reason other than "
        "earnings, who adds nothing to a couple threshold. A partner who "
        "cannot be a joint claimant has no threshold either; the amount here "
        "is what they add to the couple threshold, the pay for 35 hours at "
        "the national living wage."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 90(2) and (3)",
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
        group = person("uc_work_related_group_apart_from_earnings", period)
        groups = group.possible_values
        group_index = select(
            [
                group == groups.NO_REQUIREMENTS,
                group == groups.INTERVIEW_ONLY,
                group == groups.WORK_PREPARATION,
                group == groups.ALL_REQUIREMENTS,
            ],
            [NO_REQUIREMENTS, INTERVIEW_ONLY, WORK_PREPARATION, ALL_REQUIREMENTS],
            default=-1,
        )
        hours = threshold_hours(
            person,
            period,
            parameters,
            group_index,
            person("uc_expected_hours", period),
        )
        return gross_threshold(person, period, parameters, hours)
