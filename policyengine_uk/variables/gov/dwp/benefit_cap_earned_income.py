from policyengine_uk.model_api import *


class benefit_cap_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Earned income for the benefit cap earnings exception"
    documentation = (
        "The earned income the Universal Credit benefit cap earnings "
        "exception tests: the claimant's earned income, or a couple's "
        "combined earned income, where each person's earned income is their "
        "earnings less their own relievable pension contributions and their "
        "own income tax and National Insurance on those earnings. It leaves "
        "out any income the minimum income floor treats a self-employed "
        "person as having, and the work allowance is not deducted. It counts "
        "the same people and the same earnings as the Universal Credit award, "
        "including miscellaneous_income (see "
        "PolicyEngine/policyengine-uk#1961)."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 82(1)(a) and (4)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/82",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 55(5)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        ),
    ]

    def formula(benunit, period, parameters):
        # Reg. 82(1)(a) tests "the claimant's earned income or, if the claimant
        # is a member of a couple, the couple's combined earned income": a
        # dependant's earnings do not count. Reg. 82(4) leaves out income a
        # person is treated as having under reg. 62 (minimum income floor), so
        # this sums each claimant's actual earned income, the figure the
        # floor is compared with.
        #
        # Earnings include miscellaneous_income because the Universal Credit
        # award counts it as earned (uc_individual_earned_income_before_mif).
        # The FRS fills it with paid work, which is earned (reg. 52(a)(iii)),
        # and with royalties, trust income and overseas pensions, which
        # reg. 66(1) treats as unearned. PolicyEngine/policyengine-uk#1961
        # tracks the split; sharing the one definition moves the award and
        # this test together when it lands.
        claimants = benunit.members("is_uc_assessed_claimant", period)
        return add_for_members(
            benunit, period, ["uc_individual_earned_income_before_mif"], claimants
        )
