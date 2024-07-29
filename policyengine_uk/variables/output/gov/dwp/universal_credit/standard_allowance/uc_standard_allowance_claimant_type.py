from policyengine_uk.model_api import *


class UCClaimantType(Enum):
    SINGLE_YOUNG = "Single, under 25"
    SINGLE_OLD = "Single, 25 or over"
    COUPLE_YOUNG = "Couple, both under 25"
    COUPLE_OLD = "Couple, one over 25"


class uc_standard_allowance_claimant_type(Variable):
    value_type = Enum
    possible_values = UCClaimantType
    default_value = UCClaimantType.SINGLE_YOUNG
    entity = BenUnit
    label = "Universal Credit claimant type"
    documentation = (
        "The category of the UC claimant, assuming their eligibilty to UC"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        is_single = benunit("is_single", period)
        p = parameters(
            period
        ).gov.dwp.universal_credit.standard_allowance.claimant_type
        any_over_25 = (
            benunit("eldest_adult_age", period.this_year) >= p.age_threshold
        )
        return select(
            [
                is_single & ~any_over_25,
                is_single & any_over_25,
                ~is_single & ~any_over_25,
                ~is_single & any_over_25,
            ],
            [
                UCClaimantType.SINGLE_YOUNG,
                UCClaimantType.SINGLE_OLD,
                UCClaimantType.COUPLE_YOUNG,
                UCClaimantType.COUPLE_OLD,
            ],
        )
