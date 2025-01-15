from policyengine_uk.model_api import *

class free_childcare_15_hours_eligibility(Variable):
    value_type = bool
    entity = BenUnit
    label = "15 hours free childcare full eligibility"
    documentation = "Whether the benefit unit is eligible for 15 hours of free childcare"
    definition_period = YEAR
    
    def formula(benunit, period, parameters):
        """
        Calculate eligibility for 15 hours free childcare program.
        """
        # Age eligibility
        age_eligible = benunit.any(benunit.members("free_childcare_15_hours", period))
        
        # Income requirements
        meets_income = benunit.any(benunit.members("income_requirements", period))
        
        # Alternative eligibility
        alternative_eligible = benunit.any(benunit.members("work_eligibility_childcare", period))
        
        return (age_eligible & meets_income & alternative_eligible).astype(bool)


class free_childcare_30_hours_eligibility(Variable):
    value_type = bool
    entity = BenUnit
    label = "30 hours free childcare full eligibility"
    documentation = "Whether the benefit unit is eligible for 30 hours of free childcare"
    definition_period = YEAR
    
    def formula(benunit, period, parameters):
        """
        Calculate eligibility for 30 hours free childcare program.
        """
        # Age eligibility
        age_eligible = benunit.any(benunit.members("free_childcare_30_hours", period))
        
        # Income requirements
        meets_income = benunit.any(benunit.members("income_requirements", period))
        
        # Alternative eligibility
        alternative_eligible = benunit.any(benunit.members("work_eligibility_childcare", period))
        
        return (age_eligible & meets_income & alternative_eligible).astype(bool)