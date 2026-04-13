from policyengine_uk.model_api import *
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
        "to current-year in_HE, then non-default prior-year current_education, then prior-year in_HE."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        current_education_holder = person.get_holder("current_education")
        in_he_holder = person.get_holder("in_HE")
        age = person("age", period)
        false_array = np.zeros_like(age, dtype=bool)
        default_education = current_education_holder.variable.default_value

        has_current_education = current_education_holder.get_array(period) is not None
        has_current_in_he = in_he_holder.get_array(period) is not None
        has_prior_current_education = (
            current_education_holder.get_array(period.last_year) is not None
        )
        has_prior_in_he = in_he_holder.get_array(period.last_year) is not None

        current_education = person("current_education", period)
        prior_current_education = person("current_education", period.last_year)
        current_in_he = person("in_HE", period)
        prior_in_he = person("in_HE", period.last_year)

        current_education_is_explicit = (
            current_education != default_education if has_current_education else false_array
        )
        prior_current_education_is_explicit = (
            prior_current_education != default_education
            if has_prior_current_education
            else false_array
        )

        current_education_is_he = current_education == EducationType.TERTIARY
        prior_current_education_is_he = (
            prior_current_education == EducationType.TERTIARY
        )

        return select(
            [
                current_education_is_explicit,
                current_in_he if has_current_in_he else false_array,
                prior_current_education_is_explicit,
                prior_in_he if has_prior_in_he else false_array,
            ],
            [
                current_education_is_he,
                np.ones_like(age, dtype=bool),
                prior_current_education_is_he,
                np.ones_like(age, dtype=bool),
            ],
            default=false_array,
        )
