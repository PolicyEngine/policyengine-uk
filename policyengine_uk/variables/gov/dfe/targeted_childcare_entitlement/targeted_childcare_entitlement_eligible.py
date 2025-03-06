from policyengine_uk.model_api import *

class targeted_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligibility for targeted childcare entitlement"
    definition_period = YEAR
    
    adds = [
        "meets_universal_credit_criteria_for_targeted_childcare_entitlement", 
        "meets_tax_credit_criteria_for_targeted_childcare_entitlement"
    ]
    
    def formula(benunit, period, parameters):
        # Check if household is in England
        country = benunit.household("country", period)
        in_england = country == country.possible_values.ENGLAND
        
        # Check other qualifying benefits
        p = parameters(period).gov.dfe.targeted_childcare_entitlement
        has_qualifying_benefits = add(benunit, period, p.qualifying_benefits) > 0
        
        # Use the variable names directly instead of self.adds
        meets_any_criteria = add(
            benunit, 
            period, 
            [
                "meets_universal_credit_criteria_for_targeted_childcare_entitlement",
                "meets_tax_credit_criteria_for_targeted_childcare_entitlement"
            ]
        ) > 0
        
        return (meets_any_criteria | has_qualifying_benefits) & in_england