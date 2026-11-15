from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import (
    latest_supplied_input_period,
    supplied_input,
)
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
        "Only supplied inputs count, never current_education's age-based fallback."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        # Evidence is what was supplied (dataset or situation inputs), never a
        # value the model calculated, such as current_education's age-based
        # fallback. Testing whether a value is stored instead would depend on
        # what had already been calculated.
        age = person("age", period)
        false_array = np.zeros_like(age, dtype=bool)
        true_array = np.ones_like(age, dtype=bool)
        default_education = EducationType.NOT_IN_EDUCATION

        def education_evidence(education):
            # (explicit, higher education) for a supplied current_education.
            if education is None:
                return false_array, false_array
            return (
                education != default_education,
                education == EducationType.TERTIARY,
            )

        current_education_is_explicit, current_education_is_he = education_evidence(
            supplied_input(person, "current_education", period)
        )
        current_in_he = supplied_input(person, "in_HE", period)

        # Prior-year evidence is the latest supplied for an earlier year, so a
        # year past the data keeps the data's last enrolment.
        prior_education_period = latest_supplied_input_period(
            person, "current_education", period
        )
        prior_current_education_is_explicit, prior_current_education_is_he = (
            education_evidence(
                supplied_input(person, "current_education", prior_education_period)
                if prior_education_period is not None
                else None
            )
        )
        prior_in_he_period = latest_supplied_input_period(person, "in_HE", period)
        prior_in_he = (
            supplied_input(person, "in_HE", prior_in_he_period)
            if prior_in_he_period is not None
            else None
        )

        return select(
            [
                current_education_is_explicit,
                false_array if current_in_he is None else current_in_he,
                prior_current_education_is_explicit,
                false_array if prior_in_he is None else prior_in_he,
            ],
            [
                current_education_is_he,
                true_array,
                prior_current_education_is_he,
                true_array,
            ],
            default=false_array,
        )
