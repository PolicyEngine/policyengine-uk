from policyengine_uk.model_api import *


class pension_credit_child_minimum_guarantee_addition(Variable):
    label = "Pension Credit child-related addition"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IIA"

    def formula(benunit, period, parameters):
        person = benunit.members
        is_child = person("is_child_or_QYP", period)
        gc = parameters(period).gov.dwp.pension_credit.guarantee_credit
        standard_disability_benefits = gc.child.disability.eligibility
        severe_disability_benefits = gc.child.disability.severe.eligibility
        receives_disability_benefits = (
            add(person, period, standard_disability_benefits) > 0
        )
        receives_severe_disability_benefits = (
            add(person, period, severe_disability_benefits) > 0
        )
        is_standard_disabled = (
            receives_disability_benefits & ~receives_severe_disability_benefits
        )
        is_not_disabled = ~receives_disability_benefits
        per_child_amount = select(
            [
                is_child & is_not_disabled,
                is_child & is_standard_disabled,
                is_child & receives_severe_disability_benefits,
            ],
            [
                gc.child.amount,
                gc.child.amount + gc.child.disability.amount,
                gc.child.amount + gc.child.disability.severe.amount,
            ],
            default=0,
        )
        return benunit.sum(per_child_amount) * WEEKS_IN_YEAR
