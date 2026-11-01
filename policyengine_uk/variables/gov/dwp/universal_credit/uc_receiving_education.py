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
        "where they have a student loan or grant for their maintenance "
        "(reg. 12(2)(b)), which it reads from "
        "has_education_maintenance_funding; or where they are a qualifying "
        "young person (reg. 12(1A)), after the Universal Credit "
        "(Transitional Provisions) Regulations 2014 reg. 28 "
        "(is_qualifying_young_person_for_uc_education). A person with "
        "is_in_full_time_education false is not receiving education in the "
        "model, so it does not apply reg. 12(1A) to a qualifying young "
        "person outside full-time education, or reg. 12(4) to a course that "
        "is incompatible with a work-related requirement. Nor does it apply "
        "the exception in reg. 12(1A) for a relevant training scheme. Under "
        "reg. 13 a person undertakes a course from its first day to its "
        "last, vacations included, unless they abandon it or the "
        "establishment dismisses them; the model applies the input to the "
        "whole year. The Universal Credit Regulations (Northern Ireland) "
        "2016 reg. 12 sets the same test, except that its reg. 12(1) has no "
        "exception for a training scheme."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/12",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/13",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/68",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
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
        # provided for the person's maintenance" (reg. 2 takes both terms
        # from reg. 68(7)).
        maintenance_funding = person("has_education_maintenance_funding", period)
        # Reg. 12(1A): "A qualifying young person is to be treated as
        # receiving education", whatever the course. SI 2014/1230 reg. 28
        # applies first, so a person entitled to an existing benefit takes
        # the route in reg. 12(2).
        qualifying_young_person = person(
            "is_qualifying_young_person_for_uc_education", period
        )
        return full_time & (advanced | maintenance_funding | qualifying_young_person)
