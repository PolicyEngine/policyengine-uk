from policyengine_uk.model_api import *


class tax_free_childcare_program_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Tax-Free Childcare program eligibility"
    documentation = "Whether the person's benefit unit meets the incompatibility conditions for tax-free childcare"
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.tax_free_childcare
        countable_programs = add(
            person.benunit,
            period,
            p.incompatible_benefits,
        )
        return countable_programs == 0
