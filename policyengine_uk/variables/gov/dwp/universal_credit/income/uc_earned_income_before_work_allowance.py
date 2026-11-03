from policyengine_uk.model_api import *


class uc_earned_income_before_work_allowance(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit earned income before the work allowance"
    documentation = (
        "The claimant's earned income, or joint claimants' combined earned "
        "income, as Universal Credit calculates it (UC Regs 2013 Part 6 "
        "Chapter 2): each claimant's earnings less their own pension "
        "contributions, income tax and National Insurance, or the amount the "
        "minimum income floor treats them as having. Earnings of a child, a "
        "qualifying young person or anyone else in the benefit unit who is "
        "not a claimant do not count. The work allowance, which belongs to "
        "the award calculation in reg. 22, is not deducted. Rules that refer "
        "to the Universal Credit calculation of earned income use this amount."
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
        dict(
            title="Welfare Reform Act 2012 s. 8(3) and (4)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/8",
        ),
    ]

    def formula(benunit, period, parameters):
        # Reg. 22(1)(b) takes "the claimant's earned income (or, in the case
        # of joint claimants, their combined earned income)", so only the
        # claimants' earned income counts.
        claimants = benunit.members("is_uc_assessed_claimant", period)
        return add_for_members(
            benunit, period, ["uc_individual_earned_income"], claimants
        )
