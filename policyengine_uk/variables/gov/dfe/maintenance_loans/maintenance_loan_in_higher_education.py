from policyengine_uk.model_api import *
from policyengine_uk.utils.inputs import input_periods, latest_input_period_before
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)


class maintenance_loan_in_higher_education(Variable):
    value_type = bool
    entity = Person
    label = "In higher education for maintenance loan purposes"
    documentation = (
        "Whether the person has explicit higher-education evidence for maintenance loan modelling. "
        "Non-default current-year current_education takes precedence over in_HE; otherwise the model falls back "
        "to current-year in_HE, then the latest earlier non-default current_education, then the latest earlier in_HE. "
        "Only entered values count, never current_education's age-based fallback."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        # Evidence is what was entered (dataset or situation inputs), never a
        # value the model calculated, such as current_education's age-based
        # fallback. Testing whether a value is stored instead would depend on
        # what had already been calculated.
        simulation = person.simulation
        age = person("age", period)
        false_array = np.zeros_like(age, dtype=bool)
        default_education = EducationType.NOT_IN_EDUCATION

        current_education_is_explicit = false_array
        current_education_is_he = false_array
        if period in input_periods(simulation, "current_education"):
            current_education = person("current_education", period)
            current_education_is_explicit = current_education != default_education
            current_education_is_he = current_education == EducationType.TERTIARY

        current_in_he = (
            person("in_HE", period)
            if period in input_periods(simulation, "in_HE")
            else false_array
        )

        # Prior-year evidence is the latest entered for an earlier year, so a
        # year past the data keeps the data's last enrolment.
        prior_current_education_is_explicit = false_array
        prior_current_education_is_he = false_array
        prior_education_period = latest_input_period_before(
            simulation, "current_education", period
        )
        if prior_education_period is not None:
            prior_current_education = person(
                "current_education", prior_education_period
            )
            prior_current_education_is_explicit = (
                prior_current_education != default_education
            )
            prior_current_education_is_he = (
                prior_current_education == EducationType.TERTIARY
            )

        prior_in_he_period = latest_input_period_before(simulation, "in_HE", period)
        prior_in_he = (
            person("in_HE", prior_in_he_period)
            if prior_in_he_period is not None
            else false_array
        )

        return select(
            [
                current_education_is_explicit,
                current_in_he,
                prior_current_education_is_explicit,
                prior_in_he,
            ],
            [
                current_education_is_he,
                np.ones_like(age, dtype=bool),
                prior_current_education_is_he,
                np.ones_like(age, dtype=bool),
            ],
            default=false_array,
        )
