from policyengine_uk.model_api import *


class uc_earned_income_before_work_allowance(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit earned income before the work allowance"
    documentation = (
        "The benefit unit's earned income as Universal Credit calculates it "
        "(UC Regs 2013 Part 6 Chapter 2): each person's earnings less their "
        "own pension contributions, income tax and National Insurance, or "
        "the amount the minimum income floor treats them as having. The work "
        "allowance, which belongs to the award calculation in reg. 22, is "
        "not deducted. Rules that refer to the Universal Credit calculation "
        "of earned income use this amount."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 52",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/52",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 22(1)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/22",
        ),
    ]

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant and partner and, as the model did
        # before, the programme's own children or young persons. The regulations count
        # only the claimant's and partner's (UC Regs 2013 reg 22); dropping dependants'
        # own income is a follow-up. Anyone else in the benefit unit does not count.
        person = benunit.members
        members = person("is_claimant_or_partner", period) | person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        return add_for_members(
            benunit, period, ["uc_individual_earned_income"], members
        )
