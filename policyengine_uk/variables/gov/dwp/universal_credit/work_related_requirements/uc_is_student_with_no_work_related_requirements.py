from policyengine_uk.model_api import *


class uc_is_student_with_no_work_related_requirements(Variable):
    value_type = bool
    entity = Person
    label = "Student subject to no Universal Credit work-related requirements"
    documentation = (
        "Whether the claimant is a student whom the Universal Credit "
        "Regulations 2013 reg. 89(1)(da) or (e) puts in the group subject to "
        "no work-related requirements: a member of a couple entitled under "
        "reg. 3(2)(b), or a claimant exempt from the education condition "
        "under reg. 14, with student income taken into account in the award; "
        "or a claimant under 21 in non-advanced education without parental "
        "support. A part-time postgraduate loan does not count as student "
        "income here (reg. 89(4)). An input: the model does not assess "
        "student income for Universal Credit."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/89"
    definition_period = YEAR
    default_value = False
