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
    adds = ["uc_individual_earned_income"]
