from policyengine_uk.model_api import *


class incompatibilities_childcare_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Tax-Free Childcare Exclusions"
    documentation = "Whether the person's benefit unit meets the incompatibility conditions for tax-free childcare (not receiving WTC, CTC, or UC)"
    definition_period = YEAR

    def formula(person, period, parameters):
        """
        Calculate eligibility based on incompatible benefits.
        
        Returns:
            bool: True if eligible (no incompatible benefits received), False if receiving any incompatible benefits
        """
        # Get the benefit unit the person belongs to
        benunit = person.benunit
        
        # Check if receiving any of the mutually exclusive benefits
        has_wtc = benunit("working_tax_credit", period) > 0
        has_ctc = benunit("child_tax_credit", period) > 0
        has_uc = benunit("universal_credit", period) > 0

        # Returns True when person's benefit unit does NOT receive any of these benefits
        return ~(
            has_wtc |
            has_ctc |
            has_uc
        )