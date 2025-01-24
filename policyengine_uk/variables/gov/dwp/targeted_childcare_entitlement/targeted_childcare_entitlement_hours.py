from policyengine_uk.model_api import *

class targeted_childcare_entitlement_hours(Variable):
   value_type = float
   entity = BenUnit
   label = "targeted childcare entitlement hours per year"
   documentation = "Number of free childcare hours per year the benefit unit is entitled to"
   definition_period = YEAR
   unit = "hour"

   def formula(benunit, period, parameters):
       """Calculate number of free hours the benefit unit is entitled to.
       
       Args:
           benunit: The benefit unit
           period: The time period
           parameters: Policy parameters

       Returns:
           float: Number of free childcare hours per year
       """
       # Get age eligibility status for targeted entitlement
       targeted_eligible_age = benunit(
           "targeted_childcare_entitlement_eligibility",
           period
       )

       # Get eligibility status for targeted entitlement
       targeted_eligible = benunit(
           "targeted_childcare_entitlement_benefits_eligible", 
           period
       )

       # Use hours directly from parameters file
       hours = parameters(
           period
       ).gov.dwp.targeted_childcare_entitlement.hours_per_year

       # Return hours if either eligible, 0 if not
       return where(targeted_eligible_age | targeted_eligible, hours, 0)