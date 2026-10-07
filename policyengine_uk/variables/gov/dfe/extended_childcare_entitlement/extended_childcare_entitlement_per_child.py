from policyengine_uk.model_api import *


class extended_childcare_entitlement_per_child(Variable):
    value_type = float
    entity = Person
    label = "extended childcare entitlement for this child"
    documentation = (
        "The annual value of the working parent hours for this child, over and "
        "above the universal (3- and 4-year-old) and targeted (2-year-old) "
        "hours the child also gets. The extended hours parameter gives the "
        "child's total funded hours as a working parent's child (30 a week for "
        "a 3- or 4-year-old, universal hours included), and Childcare Act 2016 "
        "s.1(6) counts the universal or targeted hours towards that total. So "
        "the child's funded hours are the larger of the universal or targeted "
        "hours and the working parent total, never both added in full, and "
        "becoming eligible never removes the universal or targeted hours."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "extended_childcare_entitlement_eligible"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2016/5/section/1",
        "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe
        age = person("age", period)

        # Only qualifying children of working parents (SI 2022/1134 reg 13)
        # receive the entitlement's hours.
        qualifying_child = person(
            "extended_childcare_entitlement_qualifying_child", period
        )
        weekly_hours = (
            p.extended_childcare_entitlement.hours.calc(age) * qualifying_child
        )

        # Hours actually used: the child's own limit and the family's limit.
        max_hours_used = person("max_free_entitlement_hours_used", period)
        family_max_hours = person.benunit(
            "maximum_extended_childcare_hours_usage", period
        )
        weekly_hours_used = min_(min_(weekly_hours, max_hours_used), family_max_hours)
        total_value = (
            weekly_hours_used * p.weeks_per_year * p.childcare_funding_rate.calc(age)
        )

        # Childcare Act 2016 s.1(6)(a): the childcare available under the
        # duty in Childcare Act 2006 s.7(1) counts towards the 30 hours. DfE's
        # statutory guidance (April 2026, "Amount of free childcare for
        # children of working parents" and para A1.11) gives a child eligible
        # for both 15 universal or Early Learning for 2-year-olds hours plus
        # 15 working parent hours. The working parent hours are therefore the
        # part of the total above the universal and targeted hours.
        universal_or_targeted = person(
            "universal_childcare_entitlement", period
        ) + person("targeted_childcare_entitlement", period)
        # Rounded to the penny: the universal and targeted values are stored
        # in single precision, so a total equal to them would otherwise leave
        # a fraction of a penny.
        return max_(np.round(total_value - universal_or_targeted, 2), 0)
