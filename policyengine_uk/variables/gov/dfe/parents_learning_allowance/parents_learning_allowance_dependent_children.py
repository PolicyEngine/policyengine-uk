from policyengine_uk.model_api import *


class parents_learning_allowance_dependent_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Dependent children for Parents' Learning Allowance"
    documentation = (
        "Number of dependent children of the student (Education (Student "
        "Support) Regulations 2011 regs 42 and 46). The law sets no age limit."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2011/1986/regulation/46"

    def formula(benunit, period, parameters):
        return add(benunit, period, ["is_dependent_child_for_student_support"])
