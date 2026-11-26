from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dfe.education_maintenance_allowance.ema_weekly_award import (
    ema_parameters,
    ema_routes,
)


class ema_course_eligible(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    default_value = False
    label = "EMA course eligible"
    documentation = (
        "Course and provider conditions for the selected scoped EMA route, separate "
        "from income, residence and attendance."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )

    def formula(person, period, parameters):
        shared, wales, scotland, ni = ema_parameters(parameters, period)
        in_wales, in_scotland, in_ni = ema_routes(person, period, shared)
        course = person("ema_course_type", period)
        types = course.possible_values
        school = course == types.SCHOOL
        college = course == types.FURTHER_EDUCATION
        preparation = course == types.PREPARATION_FOR_LIFE_OR_WORK
        full_time = person("ema_course_is_full_time", period)
        hours = person("ema_course_learning_hours", period)
        level = person("ema_qualification_level", period)
        recognised = person("ema_provider_approved", period) & ~person(
            "ema_incompatible_course_funding", period
        )
        welsh_qualification = (
            (school | college)
            & (level >= 0)
            & (level <= wales.maximum_qualification_level)
            & (
                person("ema_course_duration_weeks", period)
                >= wales.minimum_course_weeks
            )
        )
        welsh = (
            full_time
            & (hours >= wales.minimum_learning_hours)
            & (welsh_qualification | preparation)
        )
        # Highland permits the documented hours/mode exception only for the
        # specified vulnerable-student or young-carer circumstances.
        flexible_category = np.isin(
            person("ema_extended_duration_category", period).decode_to_str(),
            list(scotland.extended_duration_categories),
        )
        flexible_arrangement = (
            person("ema_flexible_learning_arrangement", period) & flexible_category
        )
        scottish = school & (
            (full_time & (hours >= scotland.minimum_learning_hours))
            | flexible_arrangement
        )
        northern_irish = (
            ((school & full_time) | (college & (hours >= ni.minimum_college_hours)))
            & (level >= 0)
            & (level <= ni.maximum_qualification_level)
        )
        return recognised & (
            (in_wales & welsh) | (in_scotland & scottish) | (in_ni & northern_irish)
        )
