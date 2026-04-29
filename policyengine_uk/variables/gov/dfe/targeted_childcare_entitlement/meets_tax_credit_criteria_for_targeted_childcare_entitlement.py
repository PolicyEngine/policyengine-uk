from policyengine_uk.model_api import *


class meets_tax_credit_criteria_for_targeted_childcare_entitlement(Variable):
    value_type = bool
    entity = BenUnit
    label = "meets Tax Credit criteria for targeted childcare entitlement"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dfe.targeted_childcare_entitlement
        tax_credit_criteria = [
            "meets_working_tax_credit_criteria_for_targeted_childcare_entitlement",
            "meets_child_tax_credit_criteria_for_targeted_childcare_entitlement",
            "working_tax_credit_run_on",
        ]
        active_tax_credit_criteria = [
            variable
            for variable in tax_credit_criteria
            if variable in p.qualifying_criteria
        ]
        if not active_tax_credit_criteria:
            return False
        return add(benunit, period, active_tax_credit_criteria) > 0
