from policyengine_uk.model_api import *


class tax_free_childcare_program_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Tax-Free Childcare program eligibility"
    documentation = "Whether the person's benefit unit meets the incompatibility conditions for tax-free childcare (not receiving WTC, CTC, or UC)"
    definition_period = YEAR

    def formula(person, period, parameters):
        credits_list = [
            "working_tax_credit",
            "child_tax_credit",
            "universal_credit",
        ]
        countable_programs = add(
            person.benunit,
            period,
            credits_list,
        )
        return countable_programs == 0
