from policyengine_uk.model_api import *


class extended_childcare_entitlement_qualifying_child(Variable):
    value_type = bool
    entity = Person
    label = "qualifying child of working parents for the extended childcare entitlement"
    documentation = (
        "A young child for whom working parents can take up the extended "
        "childcare entitlement: under compulsory school age and in England "
        "(Childcare Act 2016 s.1(2)(a)-(b)), and at least the minimum age and "
        "not looked after by a local authority (SI 2022/1134 reg 13(2); "
        "SI 2016/1257 reg 3(1) before 1 December 2022). A child in a "
        "reception class does not count: its school place meets the "
        "entitlement (early_years_child_in_school)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2016/5/section/1",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/13",
        "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe
        age = person("age", period)

        # Compulsory school age starts at the lowest age in the scale
        # (Education Act 1996 s.8); a young child has not reached it.
        compulsory_school_age = p.compulsory_school_age
        compulsory_school_age_start = min(
            threshold
            for threshold, is_compulsory in zip(
                compulsory_school_age.thresholds, compulsory_school_age.amounts
            )
            if is_compulsory
        )
        under_compulsory_school_age = age < compulsory_school_age_start

        country = person.household("country", period)
        in_england = country == country.possible_values.ENGLAND

        meets_minimum_age = (
            age >= p.extended_childcare_entitlement.young_child_minimum_age
        )
        not_looked_after = ~person("is_looked_after_by_local_authority", period)

        # A child in a state-funded or council-funded reception class is
        # still under compulsory school age, but the school place meets the
        # duty: DfE's statutory guidance (April 2026, footnotes 7 and 17,
        # paras A4.8 and C.6) gives no free hours outside it. Childcare Act
        # 2016 s.1(6) splits a child's hours between this entitlement and the
        # universal one, so both leave it out.
        in_school = person("early_years_child_in_school", period)

        return (
            under_compulsory_school_age
            & in_england
            & meets_minimum_age
            & not_looked_after
            & ~in_school
        )
