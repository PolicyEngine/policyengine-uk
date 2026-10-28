from policyengine_uk.model_api import *
from policyengine_uk.utils.carers_allowance_taper import (
    carers_allowance_weekly_by_part_of_year,
)


class carers_allowance_pre_couple_limit(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance before the couple and overlap restrictions"
    documentation = (
        "The existing age, caring, earnings and take-up calculation before "
        "the same-person couple restriction and overlapping-benefit adjustment. "
        "This candidate amount is not final entitlement or payment. In the "
        "year the Budget 2026 earnings taper starts, it adds the award before "
        "the taper starts and the award under it, each for its share of the "
        "year."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/ukpga/1992/7/section/70",
    )

    def formula(person, period, parameters):
        parts = carers_allowance_weekly_by_part_of_year(person, period, parameters)
        return sum(share * weekly * WEEKS_IN_YEAR for share, weekly in parts)
