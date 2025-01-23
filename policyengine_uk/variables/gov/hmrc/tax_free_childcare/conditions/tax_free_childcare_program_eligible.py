from policyengine_uk.model_api import *


class tax_free_childcare_program_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Tax-Free Childcare program eligibility"
    documentation = "Whether the person's benefit unit meets the incompatibility conditions for tax-free childcare (not receiving WTC, CTC, or UC)"
    definition_period = YEAR

    def formula(person, period, parameters):
        """
        Calculate eligibility based on incompatible benefits.

        Returns:
            bool: True if eligible (no incompatible benefits received), False if receiving any incompatible benefits
        """
        countable_programs = add(person.benunit, period, ["working_tax_credit", "child_tax_credit", "universal_credit"])
        return countable_programs == 0