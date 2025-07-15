from policyengine_uk.model_api import *


class benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Benefit cap for the family"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        is_single_adult = benunit("num_adults", period) == 1
        has_children = benunit("num_children", period) > 0
        single_claimant = is_single_adult & ~has_children
        household_region = benunit.members.household("region", period)
        region = benunit.value_from_first_person(household_region)
        regions = household_region.possible_values
        in_london = region == regions.LONDON
        cap = parameters(period).gov.dwp.benefit_cap
        rate = select(
            [
                single_claimant & in_london,
                single_claimant & ~in_london,
                ~single_claimant & in_london,
                ~single_claimant & ~in_london,
            ],
            [
                cap.single.in_london,
                cap.single.outside_london,
                cap.non_single.in_london,
                cap.non_single.outside_london,
            ],
        )
        exempt = benunit("is_benefit_cap_exempt", period)
        return where(exempt, np.inf * np.ones_like(has_children), rate)
