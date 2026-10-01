from policyengine_uk.model_api import *


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
        "includes the household head's non-dependants and their children. "
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
        child = person("is_child_for_universal_credit", period)
        no_one_responsible = (
            child | person("is_qualifying_young_person_for_universal_credit", period)
        ) & ~responsible
        # UC Regs 2013 Sch 4 para 12(A1)(a)-(b): the renter and the members of
        # their extended benefit unit, which excludes a child or qualifying
        # young person no one is responsible for (paras 9(1) and 9(2)(g));
        # (c): a child for whom the renter meets the foster parent condition.
        own = overnight_care & ~(no_one_responsible & ~child)
        # Para 9(1)(c): the household head's non-dependants from other
        # families, and their children.
        other = (
            overnight_care
            & person("is_non_dependant_of_household_head", period)
            & ~no_one_responsible
        )
        head_family = benunit.any(person("is_household_head", period))
        others = head_family * benunit.max(person.household.sum(other))
        # Para 12(9)(a)-(b): one bedroom for each condition met.
        overnight_room = benunit.any(own) | (others > 0)
        foster_room = benunit("lha_renter_meets_foster_parent_condition", period)
        return 1.0 * overnight_room + 1.0 * foster_room
