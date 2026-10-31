from policyengine_uk.model_api import *


class uc_receiving_education(Variable):
    value_type = bool
    entity = Person
    label = "Receiving education for Universal Credit"
    documentation = (
        "Whether this person is receiving education under the Universal "
        "Credit Regulations 2013 reg. 12, and so does not meet the basic "
        "condition in the Welfare Reform Act 2012 s. 4(1)(d) unless an "
        "exception applies (uc_is_excepted_from_education_condition). A "
        "person on a full-time course (is_in_full_time_education) receives "
        "education where the course is advanced education (reg. 12(2)(a)), "
        "which the model reads from tertiary current_education or in_HE; "
        "where a student loan or grant is provided for their maintenance "
        "(reg. 12(2)(b)), which it reads from student_loans or "
        "education_grants; or where they are a qualifying young person "
        "(reg. 12(1A)). education_grants can also hold grants that are not "
        "for maintenance, such as Disabled Students' Allowance. A person "
        "with is_in_full_time_education false is not receiving education in "
        "the model, so it does not apply reg. 12(1A) to a qualifying young "
        "person outside full-time education, reg. 12(4) to a course that is "
        "incompatible with a work-related requirement, or the exception in "
        "reg. 12(1A) for a relevant training scheme. Under reg. 13 a person "
        "undertakes a course from its first day to its last, vacations "
        "included, unless they abandon it or are dismissed; the model "
        "applies the input to the whole year. The Universal Credit "
        "Regulations (Northern Ireland) 2016 reg. 12 is the same, except that "
        "its reg. 12(1) has no exception for a training scheme."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/12",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/13",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/68",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/12",
    )

    def formula(person, period, parameters):
        full_time = person("is_in_full_time_education", period)
        # Reg. 12(3): a course leading to a degree, DipHE or HND, or "of a
        # standard above a general certificate of education (advanced
        # level), or above a Scottish national qualification (higher or
        # advanced higher)".
        education = person("current_education", period)
        advanced = (education == education.possible_values.TERTIARY) | person(
            "in_HE", period
        )
        # Reg. 12(2)(b): "any other full-time course of study or training at
        # an educational establishment for which a student loan or grant is
        # provided for the person's maintenance" (both defined in reg. 68(7)).
        maintenance_support = (person("student_loans", period) > 0) | (
            person("education_grants", period) > 0
        )
        # Reg. 12(1A): "A qualifying young person is to be treated as
        # receiving education", whatever the course.
        qualifying_young_person = person(
            "is_qualifying_young_person_for_universal_credit", period
        )
        return full_time & (advanced | maintenance_support | qualifying_young_person)
