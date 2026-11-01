from policyengine_uk.model_api import *


class has_education_maintenance_funding(Variable):
    value_type = bool
    entity = Person
    label = "Has a student loan or grant for maintenance on their course"
    documentation = (
        "Whether this person has a student loan or grant for their "
        "maintenance on their course of study or training. A person on a "
        "full-time course other than a course of advanced education receives "
        "education for Universal Credit when they have one (Universal Credit "
        "Regulations 2013 reg. 12(2)(b)). Reg. 2 takes both terms from reg. "
        "68(7), which defines a student loan as a loan towards a student's "
        "maintenance under the student support legislation, and a grant as "
        "any educational grant or award, except a student loan or a payment "
        "under a scheme that helps people under 21 complete courses other "
        "than advanced education. The test needs funding for maintenance, so "
        "a grant for fees, equipment or travel alone doesn't count. An input "
        "that stays false "
        "until a user or dataset sets it. The model does not derive it from "
        "student_loans or education_grants: neither says what the support "
        "pays for, and education_grants can hold grants for childcare or "
        "disability costs."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/12",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/68",
    )
