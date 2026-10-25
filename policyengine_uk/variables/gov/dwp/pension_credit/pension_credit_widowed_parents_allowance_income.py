from policyengine_uk.model_api import *


class pension_credit_widowed_parents_allowance_income(Variable):
    label = "Widowed parent's allowance counted for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    documentation = (
        "The claimant's and partner's widowed parent's allowance, each less "
        "the Sch. IV para. 7 disregard of £10 a week. Reg. 15(1) prescribes "
        "it as income, and reg. 9 does not exclude it from Savings Credit "
        "qualifying income. Reg. 14 applies Part III's references to the "
        "claimant equally to the partner, so each member's allowance gets its "
        "own £10, as each member's war pension does under para. 1. "
        "Dependants' and other benefit-unit members' allowances do not count "
        "(State Pension Credit Act 2002 s.5). The allowance is not payable "
        "from pensionable age or while the recipient lives with a partner "
        "(SSCBA 1992 s.39A(4) and (5)), so this counts reported awards."
    )
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/5",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/14",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/15",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IV/paragraph/7",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.income
        person = benunit.members
        disregard = p.widowed_parents_allowance_disregard * WEEKS_IN_YEAR
        counted = max_(person("widowed_parents_allowance", period) - disregard, 0)
        return benunit.sum(counted * person("is_claimant_or_partner", period))
