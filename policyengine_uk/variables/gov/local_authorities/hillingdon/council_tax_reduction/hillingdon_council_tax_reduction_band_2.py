from policyengine_uk.model_api import *


class hillingdon_council_tax_reduction_band_2(Variable):
    value_type = bool
    entity = BenUnit
    label = "Hillingdon CTR vulnerable Band 2"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.hillingdon.council_tax_reduction
        weekly_income = benunit(
            "hillingdon_council_tax_reduction_weekly_income", period
        )
        person = benunit.members
        num_children = benunit.sum(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
        )
        is_couple = benunit("is_couple", period)
        upper_limit = select(
            [
                num_children >= 2,
                num_children == 1,
                is_couple,
            ],
            [
                ctr.vulnerable_upper_limit.family_two_or_more_children,
                ctr.vulnerable_upper_limit.family_one_child,
                ctr.vulnerable_upper_limit.couple,
            ],
            default=ctr.vulnerable_upper_limit.single,
        )
        vulnerable = benunit("hillingdon_council_tax_reduction_vulnerable", period)
        return vulnerable & (weekly_income <= upper_limit)
