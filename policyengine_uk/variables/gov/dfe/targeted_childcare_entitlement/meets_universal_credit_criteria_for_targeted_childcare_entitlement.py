from policyengine_uk.model_api import *


class meets_universal_credit_criteria_for_targeted_childcare_entitlement(Variable):
    value_type = bool
    entity = BenUnit
    label = "meets Universal Credit criteria for targeted childcare entitlement"
    documentation = (
        "Whether the parents are entitled to Universal Credit with earned "
        "income, as Universal Credit calculates it and before the work "
        "allowance, not exceeding the limit."
    )
    definition_period = YEAR
    reference = dict(
        title=(
            "Local Authority (Duty to Secure Early Years Provision Free of "
            "Charge) Regulations 2014 reg. 1(2), (3) and (4)"
        ),
        href="https://www.legislation.gov.uk/uksi/2014/2147/regulation/1",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dfe.targeted_childcare_entitlement

        # Check if receiving Universal Credit
        uc = benunit("universal_credit", period)

        # Reg. 1(3)(a): "earned income" means income for the purposes of
        # Chapter 2 of Part 6 of the Universal Credit Regulations 2013, and
        # reg. 1(3)(c) reads the limit against a couple's combined income.
        # Chapter 2 is each person's earnings after their own tax, National
        # Insurance and pension contributions, with the minimum income floor
        # (reg. 62). The work allowance is in reg. 22 (Part 3, the award), so
        # it is not deducted here.
        earned_income = benunit("uc_earned_income_before_work_allowance", period)

        return (uc > 0) & (earned_income <= p.income_limit.universal_credit)
