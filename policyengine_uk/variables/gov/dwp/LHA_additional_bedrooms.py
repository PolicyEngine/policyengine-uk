from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_allowed_bedrooms import (
    other_family_non_dependants,
)


class LHA_additional_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "Additional bedrooms in the Universal Credit size criteria"
    documentation = (
        "One additional bedroom if anyone in the renter's extended benefit "
        "unit, or a foster child of the renter, meets the overnight care "
        "condition (see meets_lha_overnight_care_condition), however many "
        "people do; and one if the renter or a joint renter meets the foster "
        "parent condition (see lha_renter_meets_foster_parent_condition), "
        "however many children are placed. The extended benefit unit "
        "includes the household's non-dependants and their children, in the "
        "one Universal Credit claim that counts them (see "
        "uc_non_dependants_counted), as the size criteria count them (see "
        "other_family_non_dependants in LHA_allowed_bedrooms). "
        "Before 1 April 2017 only the renter could meet the overnight care "
        "condition. "
        "The disabled child and disabled person conditions, for children or "
        "couples who cannot share a bedroom, are not modelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/10",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        overnight_care = person("meets_lha_overnight_care_condition", period)
        responsible = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        no_one_responsible = (
            person("is_child_for_universal_credit", period)
            | person("is_qualifying_young_person_for_universal_credit", period)
        ) & ~responsible
        # UC Regs 2013 Sch 4 para 12(A1)(a)-(b): the renter and the members of
        # their extended benefit unit, which excludes a child or qualifying
        # young person no one is responsible for (paras 9(1) and 9(2)(g));
        # (c): a child for whom the renter meets the foster parent condition.
        foster_child = person("is_lha_foster_child", period)
        own = overnight_care & (~no_one_responsible | foster_child)
        # Para 9(1)(c): non-dependants from other families, and their
        # children, as the size criteria count them.
        other = overnight_care & other_family_non_dependants(benunit, period)
        # Universal Credit counts the household's non-dependants in one claim
        # only (para 9(2)(f); see uc_non_dependants_counted).
        counted = benunit("uc_non_dependants_counted", period)
        others = counted * benunit.max(person.household.sum(other))
        # Before 1 April 2017 (SI 2017/213 reg 6) only the renter could meet
        # the overnight care condition.
        p = parameters(period).gov.dwp.LHA
        renter = person("is_claimant_or_partner", period)
        own = where(p.overnight_care_beyond_claimant, own, overnight_care & renter)
        others = others * p.overnight_care_beyond_claimant
        # Para 12(9)(a)-(b): one bedroom for each condition met.
        overnight_room = benunit.any(own) | (others > 0)
        foster_room = benunit("lha_renter_meets_foster_parent_condition", period)
        return 1.0 * overnight_room + 1.0 * foster_room
