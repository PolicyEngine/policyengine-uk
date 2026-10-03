from policyengine_uk.model_api import *


class uc_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit earned income (after disregards and tax)"
    definition_period = YEAR
    unit = GBP

    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/22"

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant and partner and, as the model did
        # before, the programme's own children or young persons. The regulations count
        # only the claimant's and partner's (UC Regs 2013 reg 22); dropping dependants'
        # own income is a follow-up. Anyone else in the benefit unit does not count.
        person = benunit.members
        members = person("is_claimant_or_partner", period) | person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        personal_gross_earned_income = add_for_members(
            benunit, period, ["uc_mif_capped_earned_income"], members
        )
        disregards = add_for_members(
            benunit,
            period,
            ["uc_work_allowance", "tax", "pension_contributions"],
            members,
        )
        # UC does not count rent from boarders, lodgers or sub-tenants (reg
        # 66(1)), so the tax on it is not tax in respect of any employment
        # (reg 55(5)(b)) and is not deducted. The rest of `tax` is wider than
        # reg 55(5)(b) allows; that is #1942.
        disregards -= add_for_members(
            benunit, period, ["rent_a_room_income_tax_after_reductions"], members
        )
        return max_(0, personal_gross_earned_income - disregards)
