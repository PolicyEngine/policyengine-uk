from policyengine_uk.model_api import *


class targeted_childcare_entitlement_combine_benefits(Variable):
   """Determines if a benefit unit is eligible for Targeted childcare entitlement (2-year-olds) based on benefits and income.
   
   The entitlement is based on receiving qualifying benefits (like Jobseeker's Allowance, Employment Support Allowance,
   Universal Credit etc.) and meeting specific income thresholds where applicable. It also includes disability-based
   eligibility through Disability Living Allowance.
   """
   value_type = bool
   entity = BenUnit
   label = "Eligible for Targeted childcare entitlement based on benefits"
   definition_period = YEAR

   def formula(benunit, period, parameters):
       """Calculate eligibility based on benefits receipt and income thresholds.

       The formula checks multiple eligibility pathways:
       1. Receipt of means-tested benefits (Jobseeker's Allowance, Employment Support Allowance)
       2. Universal Credit with income threshold of £15,400
       3. Tax Credits with income threshold of £16,190
       4. Receipt of disability benefits
       5. Receipt of Pension Credit Guarantee

       Args:
           benunit (Entity): The benefit unit entity
           period (Period): The time period
           parameters (ParameterNode): The parameter tree

       Returns:
           bool: True if eligible through any pathway, False otherwise
       """
       # Calculate total income for the benefit unit
       benunit_income = benunit.sum(benunit.members("total_income", period))
       # Calculate benefits income to exclude from Universal Credit calculation
       benefits_income = benunit.sum(benunit.members("social_security_income", period))
       # Income excluding benefits for Universal Credit threshold check
       adjusted_income = benunit_income - benefits_income
       
       # Check if receiving income-based Jobseeker's Allowance
       receives_jobseekers = benunit("jsa_income", period) > 0

       # Check if receiving income-related Employment and Support Allowance
       receives_employment_support = benunit("esa_income", period) > 0

       # Check if receiving Universal Credit
       receives_universal_credit = benunit("universal_credit", period) > 0

       # Check if receiving Pension Credit Guarantee element
       receives_pension_credit = benunit("is_guarantee_credit_eligible", period)

       # Check if receiving Child Tax Credit
       receives_child_tax_credit = benunit("child_tax_credit", period) > 0

       # Check if receiving Working Tax Credit
       receives_working_tax_credit = benunit("working_tax_credit", period) > 0
       
       # Check if any member receives Disability Living Allowance
       receives_disability_allowance = benunit.sum(benunit.members("dla", period)) > 0

       # Check Universal Credit with £15,400 income threshold
       meets_universal_credit_income = receives_universal_credit & (adjusted_income <= 15400)

       # Check Tax Credits with £16,190 income threshold
       meets_tax_credits_income = (receives_child_tax_credit | receives_working_tax_credit) & (benunit_income <= 16190)

       # Combine all eligibility conditions
       return (
           receives_jobseekers |             # Income-based Jobseeker's Allowance
           receives_employment_support |      # Income-related Employment and Support Allowance
           meets_universal_credit_income |    # Universal Credit with income <= £15,400
           receives_pension_credit |          # Pension Credit Guarantee
           meets_tax_credits_income |         # Tax Credits with income <= £16,190
           receives_disability_allowance      # Disability Living Allowance
       )