from policyengine_uk.model_api import *


class benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Benefit cap for the family"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        single_claimant = benunit("is_benefit_cap_single_claimant_rate", period)
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
        return where(exempt, np.inf, rate)
