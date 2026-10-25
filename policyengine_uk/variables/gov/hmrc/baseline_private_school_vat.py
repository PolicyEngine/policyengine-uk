from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.private_school_vat import (
    private_school_vat_liability,
)


class baseline_private_school_vat(Variable):
    label = "baseline private school VAT"
    documentation = (
        "private_school_vat under baseline policy (the exemption, the standard "
        "rate and the reform rate), with this simulation's attendance, mean "
        "fee and share of fees bearing VAT. Holding the assumptions fixed "
        "means private_school_vat_change measures policy alone."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        # parameters.baseline is cloned before the fiscal-year conversion, so
        # it reads the exemption and rates at 1 January where the level reads
        # them at 30 April. They agree while none changes between those
        # dates; baseline_vat has the same property.
        return private_school_vat_liability(
            household,
            period,
            parameters(period).baseline.gov,
            parameters(period).gov.simulation.private_school_vat,
        )
