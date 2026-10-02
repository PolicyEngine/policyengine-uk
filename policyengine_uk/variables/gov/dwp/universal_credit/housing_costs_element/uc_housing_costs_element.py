from policyengine_uk.model_api import *


class uc_housing_costs_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit housing costs element"
    definition_period = YEAR
    unit = GBP
    documentation = (
        "Universal Credit support for rent, excluding payments for specified "
        "or temporary accommodation when "
        "in_specified_or_temporary_accommodation is supplied as True. "
        "Those payments can instead be covered by Housing Benefit."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/nisr/2016/216/schedule/1/paragraph/3",
    )

    def formula(benunit, period, parameters):
        tenure_type = benunit.value_from_first_person(
            benunit.members.household("tenure_type", period)
        )
        tenure_types = tenure_type.possible_values
        rent = benunit("benunit_rent", period)
        # Universal Credit has its own monthly national maximum, which is
        # set independently of the weekly Housing Benefit one.
        rent_cap = benunit("uc_LHA_cap", period)
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
        protected_accommodation = benunit(
            "in_specified_or_temporary_accommodation", period
        )
        return where(
            protected_accommodation,
            0,
            max_(max_housing_costs - non_dependent_deductions, 0),
        )
