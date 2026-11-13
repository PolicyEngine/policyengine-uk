from policyengine_uk.model_api import *


class has_education_maintenance_funding(Variable):
    value_type = bool
    entity = Person
    label = "Has a student loan or grant for maintenance on their course"
    documentation = (
        "Whether this person has a student loan or grant for their maintenance "
        "on their course of study or training. A person on a full-time course "
        "other than a course of advanced education receives education for "
        "Universal Credit when they have one (Universal Credit Regulations "
        "2013 reg. 12(2)(b)). DWP counts as a student loan only a loan towards "
        "a student's maintenance under the student support legislation, and as "
        "a grant any educational grant or award other than a student loan or a "
        "payment under a scheme that helps people under 21 finish non-advanced "
        "courses (reg. 68(7), applied by reg. 2). A person whose grant pays "
        "only for fees, equipment or travel doesn't meet reg. 12(2)(b). It "
        "stays false until a user or dataset sets it. The model doesn't derive "
        "it from student_loans or education_grants, since it can't tell from "
        "either amount what the support pays for."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/12",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/68",
    )
