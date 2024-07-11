from policyengine_uk.model_api import *


class uc_work_allowance(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit work allowance"
    definition_period = YEAR
    unit = GBP
    defined_for = "is_uc_work_allowance_eligible"

    def formula(benunit, period, parameters):
        p = parameters(
            period
        ).gov.dwp.universal_credit.means_test.work_allowance
        housing = benunit("uc_housing_costs_element", period)
        monthly_allowance = where(
            housing > 0,
            p.with_housing,
            p.without_housing,
        )
        return monthly_allowance * MONTHS_IN_YEAR
