from policyengine_uk.model_api import *

class meets_universal_credit_criteria_for_targeted_childcare_entitlement(Variable):
    value_type = bool
    entity = BenUnit
    label = "Meets Universal Credit criteria for targeted childcare entitlement"
    definition_period = YEAR
    
    def formula(benunit, period, parameters):
        p = parameters(period).gov.dfe.targeted_childcare_entitlement
        
        # Check if receiving Universal Credit
        uc = benunit("universal_credit", period)

        # For Universal Credit recipients, we must use the definition of "earned income"
        # The Local Authority (Duty to Secure Early Years Provision Free of Charge) (Amendment) Regulations 2018 - part 2.c
        # https://www.legislation.gov.uk/uksi/2018/146/made
        
        # Check if earned income is below threshold
        earned_income = benunit.sum(benunit.members("earned_income", period))
        
        return (uc > 0) & (earned_income <= p.max_income_uc_recipients)