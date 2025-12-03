from policyengine_uk.model_api import *


class would_claim_marriage_allowance(Variable):
    label = "Would claim Marriage Allowance"
    documentation = (
        "Whether this person would claim Marriage Allowance if eligible. "
        "Generated stochastically in the dataset using take-up rates."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to True
    default_value = True


class marriage_allowance(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2007/3/part/3/chapter/3A"
    unit = GBP

    def formula(person, period, parameters):
        marital = person("marital_status", period)
        married = marital == marital.possible_values.MARRIED
        eligible = married & person(
            "meets_marriage_allowance_income_conditions", period
        )
        transferable_amount = person(
            "partners_unused_personal_allowance", period
        )
        allowances = parameters(period).gov.hmrc.income_tax.allowances
        capped_percentage = allowances.marriage_allowance.max
        max_amount = allowances.personal_allowance.amount * capped_percentage
        amount_if_eligible_pre_rounding = min_(transferable_amount, max_amount)
        # Round up.
        rounding_increment = allowances.marriage_allowance.rounding_increment
        amount_if_eligible = (
            np.ceil(amount_if_eligible_pre_rounding / rounding_increment)
            * rounding_increment
        )
        # Use pre-generated take-up decision from dataset
        would_claim = person("would_claim_marriage_allowance", period)
        return eligible * amount_if_eligible * would_claim
