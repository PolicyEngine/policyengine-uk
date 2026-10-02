from policyengine_uk.model_api import *


class uc_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit earned income (after deductions and work allowance)"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Universal Credit Regulations 2013 reg. 22(1)(b)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/22",
    )

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant and partner and, as the model did
        # before, the programme's own children or young persons. The regulations count
        # only the claimant's and partner's (UC Regs 2013 reg 22); dropping dependants'
        # own income is a follow-up. Anyone else in the benefit unit does not count.
        person = benunit.members
        members = person("is_claimant_or_partner", period) | person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        # Each person's earned income is net of their own deductions
        # (reg. 55(5), reg. 57(2)); the work allowance then comes off the
        # combined earned income before the taper (reg. 22(1)(b)).
        earned_income = add_for_members(
            benunit, period, ["uc_individual_earned_income"], members
        )
        work_allowance = benunit("uc_work_allowance", period)
        return max_(0, earned_income - work_allowance)
