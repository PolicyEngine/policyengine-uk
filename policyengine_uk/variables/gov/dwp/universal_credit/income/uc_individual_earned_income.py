from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    couple_members,
    treated_earned_income,
)


class uc_individual_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit earned income of the person"
    documentation = (
        "The person's earned income for Universal Credit before the work "
        "allowance: their earnings less their own pension contributions, "
        "income tax and National Insurance, or the amount the minimum income "
        "floor treats them as having where that applies."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 55(5)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 57(2)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 62(2) and (3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/62",
        ),
    ]

    def formula(person, period, parameters):
        # Reg. 62 compares earned income, after the deductions, with the
        # net threshold (reg. 62(2) and (3)). The couple threshold is the
        # sum of the joint claimants' individual thresholds (reg. 90(3)(a)),
        # or the claimant's threshold and a 35-hour amount for a partner who
        # is not a joint claimant (reg. 90(3)(b)); each is in
        # uc_minimum_income_floor.
        return treated_earned_income(
            person,
            person("uc_individual_earned_income_before_mif", period),
            person("uc_minimum_income_floor", period),
            person("uc_mif_applies", period),
            couple_members(person, period),
        )
