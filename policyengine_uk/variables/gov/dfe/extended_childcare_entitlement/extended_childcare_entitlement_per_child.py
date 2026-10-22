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
        "becoming eligible never removes the universal or targeted hours. A "
        "participating child has its first funded hours allocated to the "
        "applicable universal or targeted programme even when standalone "
        "take-up of that programme is false; only the remaining hours count "
        "here. The comparison is term by term: a child old enough for only "
        "some of the year's terms (extended_childcare_entitlement_term_share) "
        "has the working parent total for those terms, set against the "
        "universal or targeted hours in the same terms."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "extended_childcare_entitlement_eligible"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2016/5/section/1",
        "https://www.legislation.gov.uk/uksi/2014/2147/regulation/3",
        "https://www.legislation.gov.uk/uksi/2014/2147/regulation/4",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/44",
        "https://www.legislation.gov.uk/uksi/2023/1330/regulation/2/made",
        "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026",
    )

    def formula(person, period, parameters):
        total_value = person("extended_childcare_entitlement_total_per_child", period)

        # Childcare Act 2016 s.1(6)(a) and SI 2022/1134 reg 44(3): the
        # childcare available under the duty in Childcare Act 2006 s.7(1)
        # counts towards the 30 hours (1,140 a year, reg 44(2)(b)). DfE's
        # statutory guidance (April 2026, "Amount of free childcare for
        # children of working parents" and para A1.11) gives a child eligible
        # for both 15 universal or Early Learning for 2-year-olds hours plus
        # 15 working parent hours. The working parent hours are therefore the
        # part of the total above the universal and targeted hours. Their
        # award formulas allocate those first funded hours even when their
        # standalone take-up flags are false (2014 regs 3-4; guidance A1.11).
        # The total covers the terms the child is old enough for. Universal
        # or targeted hours claimed on their own run all year, so only those
        # terms' share of them counts; hours allocated from working parent
        # participation fall in those terms already.
        term_share = person("extended_childcare_entitlement_term_share", period)
        universal = person("universal_childcare_entitlement", period)
        targeted = person("targeted_childcare_entitlement", period)
        claims_universal = person.benunit("would_claim_universal_childcare", period)
        claims_targeted = person.benunit("would_claim_targeted_childcare", period)
        universal_or_targeted = where(
            claims_universal, term_share * universal, universal
        ) + where(claims_targeted, term_share * targeted, targeted)
        # Rounded to the penny: the universal and targeted values are stored
        # in single precision, so a total equal to them would otherwise leave
        # a fraction of a penny.
        return max_(np.round(total_value - universal_or_targeted, 2), 0)
