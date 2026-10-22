from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.deductions._deduction_amounts import (
    reference_standard_allowance,
)


class uc_last_resort_deduction_amount(Variable):
    label = "UC deductions exempt from the statutory ceiling"
    documentation = (
        "Annual cash demand for the continuing fuel and water needs, housing costs "
        "and rent exceptions in Schedule 6 paragraph 4(3)-(4). Excludes child "
        "maintenance. An explicit amount overrides the legacy approximation, which "
        "treats latent demand above the calibration cap as last resort cash at "
        "the same year's unreformed allowance. The observed aggregate does not "
        "separately identify these legal heads."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2013/380/schedule/6/paragraph/4"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.simulation.uc_deductions
        excess = max_(
            benunit("uc_latent_deduction_rate", period) - p.calibration_cap, 0
        )
        return excess * reference_standard_allowance(benunit, period, parameters)
