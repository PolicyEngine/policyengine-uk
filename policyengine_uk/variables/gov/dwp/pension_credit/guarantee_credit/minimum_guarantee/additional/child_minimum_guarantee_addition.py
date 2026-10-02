from policyengine_uk.model_api import *


class child_minimum_guarantee_addition(Variable):
    label = "Child-related addition"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IIA",
    )

    def formula(benunit, period, parameters):
        gc = parameters(period).gov.dwp.pension_credit.guarantee_credit
        # SPC Regs 2002 reg 6(6)(d) and Schedule IIA apply from 1 February
        # 2019 (SI 2018/676 reg 2).
        if not gc.child.in_effect:
            return benunit.empty_array()
        person = benunit.members
        is_child_or_qualifying_young_person = person(
            "is_child_or_qualifying_young_person_for_pension_credit", period
        )
        child_index = (
            person.get_rank(
                person.benunit,
                -person("age", period),
                condition=is_child_or_qualifying_young_person,
            )
            + 1
        )
        first_child_born_before_2017 = (child_index == 1) & (
            person("birth_year", period) < 2017
        )
        standard_disability_benefits = gc.child.disability.eligibility
        severe_disability_benefits = gc.child.disability.severe.eligibility
        is_disabled = add(person, period, standard_disability_benefits) > 0
        is_severely_disabled = add(person, period, severe_disability_benefits) > 0
        is_standard_disabled = is_disabled & ~is_severely_disabled
        is_not_disabled = ~is_disabled
        child_addition = where(
            first_child_born_before_2017,
            gc.child.first.addition,
            gc.child.addition,
        )
        per_child_amount = (
            select(
                [
                    is_child_or_qualifying_young_person & is_not_disabled,
                    is_child_or_qualifying_young_person & is_standard_disabled,
                    is_child_or_qualifying_young_person & is_severely_disabled,
                ],
                [
                    child_addition,
                    child_addition + gc.child.disability.addition,
                    child_addition + gc.child.disability.severe.addition,
                ],
            )
            * WEEKS_IN_YEAR
        )
        # Reg 6(6)(d) applies Schedule IIA "except where paragraph (11)
        # applies", which is "the case of a person who is awarded, or who is
        # treated as having an award of, a tax credit" (reg 6(11)): child tax
        # credit or working tax credit (reg 6(17)). The tax credit award then
        # carries the support for the child. Reg 6(12) and (13) treat an
        # award as continuing from the start of a tax year until it is
        # renewed or finalised, and reg 6(14) to (16) end the amount when an
        # award is made late; on the model's whole-year awards, both affect
        # only part of a year, and are not modelled.
        has_tax_credit_award = benunit("has_tax_credit_award", period)
        return benunit.sum(per_child_amount) * ~has_tax_credit_award
