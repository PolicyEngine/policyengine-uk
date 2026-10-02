from policyengine_uk.model_api import *


class benefit_cap_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Earned income for the benefit cap earnings exception"
    documentation = (
        "The earned income the Universal Credit benefit cap earnings "
        "exception tests: each person's earnings less their own pension "
        "contributions, income tax and National Insurance, summed over the "
        "benefit unit. It leaves out any income the minimum income floor "
        "treats a self-employed person as having, and the work allowance is "
        "not deducted."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Universal Credit Regulations 2013 reg. 82(1)(a) and (4)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/82",
    )
    # Reg. 82(1)(a) tests "the claimant's earned income or, if the claimant
    # is a member of a couple, the couple's combined earned income". Reg.
    # 82(4) leaves out income a person is treated as having under reg. 62
    # (minimum income floor), so this sums each person's actual earned income.
    # It counts the same earnings as the UC award does, including
    # miscellaneous_income: in the FRS that is mainly odd-job pay (reg.
    # 52(a)(iii) "any other paid work"), though it also holds some income
    # reg. 66(1)(m) treats as unearned, such as royalties. Splitting those out
    # will move the award and this test together.
    adds = ["uc_individual_earned_income_before_mif"]
