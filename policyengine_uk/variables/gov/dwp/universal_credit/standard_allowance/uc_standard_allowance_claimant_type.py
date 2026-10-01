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
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/36"

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant = person("is_uc_claimant", period)
        is_single = add(benunit, period, ["is_uc_claimant"]) <= 1
        p = parameters(period).gov.dwp.universal_credit.standard_allowance.claimant_type
        eldest_claimant_age = benunit.max(
            where(claimant, person("age", period.this_year), 0)
        )
        any_over_25 = eldest_claimant_age >= p.age_threshold
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
            default=UCClaimantType.SINGLE_YOUNG,
        )
