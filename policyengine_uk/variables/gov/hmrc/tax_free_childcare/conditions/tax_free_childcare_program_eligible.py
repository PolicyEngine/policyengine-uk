from policyengine_uk.model_api import *


class tax_free_childcare_program_eligible(Variable):
    value_type = bool
    entity = Person
    label = "tax-free childcare program eligibility"
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.tax_free_childcare
        countable_programs = add(
            person.benunit,
            period,
            p.disqualifying_benefits,
        )
        return countable_programs == 0
