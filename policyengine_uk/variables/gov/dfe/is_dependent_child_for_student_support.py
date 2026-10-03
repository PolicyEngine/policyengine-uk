from policyengine_uk.model_api import *


class is_dependent_child_for_student_support(Variable):
    """Dependent child of a student for student support in England.

    A dependent child is a child of the student or of their partner, or one the
    student has parental responsibility for, who is wholly or mainly
    financially dependent on the student (Education (Student Support)
    Regulations 2011 reg 42(1)). The regulations set no age limit; each grant
    applies its own (for example, Childcare Grant ages under reg 45(2)).

    Financial dependence is not observed, so the children and young persons in
    the student's benefit unit (everyone other than the claimant or partner)
    stand in for it.
    """

    value_type = bool
    entity = Person
    label = "Dependent child for student support"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2011/1986/regulation/42"

    def formula(person, period, parameters):
        return ~person("is_claimant_or_partner", period)
