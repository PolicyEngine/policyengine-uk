from policyengine_uk.model_api import *


class uc_maximum_reduction(Variable):
    label = "UC maximum combined reduction"
    documentation = (
        "Most that benefit cap reductions and deductions combined may take "
        "off a Universal Credit award under the protected minimum floor: "
        "(1 - floor) x the standard allowance. Infinite when the floor is "
        "zero - the value under current law, which has no such floor - so "
        "reductions are unlimited."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        # A protected minimum floor (zero under current law) caps combined
        # benefit cap reductions and deductions at (1 - floor) x the standard
        # allowance, per JRF's protected minimum floor design (their worked
        # example limits the reduction itself to 15% of the standard
        # allowance). Zero means reductions are unlimited.
        floor_rate = parameters(
            period
        ).gov.dwp.universal_credit.deductions.protected_floor
        standard_allowance = benunit("uc_standard_allowance", period)
        # A floor above 1 would make the allowance negative; subtracting a
        # negative reduction would add money to the award. Clamp at zero,
        # where the floor protects the whole standard allowance.
        return where(
            floor_rate > 0,
            max_((1 - floor_rate) * standard_allowance, 0),
            np.inf,
        )
