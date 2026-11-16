from policyengine_uk.model_api import *


class marriage_allowance_if_income_conditions_met(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance if the income conditions are met"
    documentation = (
        "The amount of personal allowance transferred to this person if they "
        "meet the income conditions (ITA 2007 s. 55B(2)(b) and (ba)). It "
        "reads neither those conditions nor the share of reliefs and "
        "allowances, so the search for that share can read it."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2007/3/part/3/chapter/3A"
    unit = GBP

    def formula(person, period, parameters):
        marital = person("marital_status", period)
        married = marital == marital.possible_values.MARRIED
        # The election is between spouses or civil partners (ITA 2007
        # s.55C(1)(a)): the claimant and partner of a married benefit unit,
        # never their children.
        spouse_or_civil_partner = person("is_claimant_or_partner", period)
        transferable_amount = person("partners_unused_personal_allowance", period)
        allowances = parameters(period).gov.hmrc.income_tax.allowances
        capped_percentage = allowances.marriage_allowance.max
        max_amount = allowances.personal_allowance.amount * capped_percentage
        amount_if_eligible_pre_rounding = max_(min_(transferable_amount, max_amount), 0)
        # Round up.
        rounding_increment = allowances.marriage_allowance.rounding_increment
        amount_if_eligible = (
            np.ceil(amount_if_eligible_pre_rounding / rounding_increment)
            * rounding_increment
        )
        # Use pre-generated take-up decision from dataset
        would_claim = person("would_claim_marriage_allowance", period)
        return married * spouse_or_civil_partner * amount_if_eligible * would_claim
