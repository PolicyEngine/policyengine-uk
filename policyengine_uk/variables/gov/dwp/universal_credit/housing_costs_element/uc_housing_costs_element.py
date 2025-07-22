from policyengine_uk.model_api import *


class uc_housing_costs_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit housing costs element"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        tenure_type = benunit.value_from_first_person(
            benunit.members.household("tenure_type", period)
        )
        tenure_types = tenure_type.possible_values
        rent = benunit("benunit_rent", period)
        rent_cap = benunit("LHA_cap", period)
        capped_rent_amount = min_(rent_cap, rent)
        max_housing_costs = select(
            [
                (tenure_type == tenure_types.RENT_FROM_COUNCIL)
                | (tenure_type == tenure_types.RENT_FROM_HA),
                tenure_type == tenure_types.RENT_PRIVATELY,
            ],
            [rent, capped_rent_amount],
            default=0,
        )
        non_dependent_deductions = benunit("uc_non_dep_deductions", period)
        return max_housing_costs - non_dependent_deductions
