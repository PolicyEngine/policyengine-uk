from policyengine_uk.model_api import *


class child_minimum_guarantee_addition(Variable):
    label = "Child-related addition"
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
        is_disabled = add(person, period, standard_disability_benefits) > 0
        is_severely_disabled = (
            add(person, period, severe_disability_benefits) > 0
        )
        is_standard_disabled = is_disabled & ~is_severely_disabled
        is_not_disabled = ~is_disabled
        per_child_amount = (
            select(
                [
                    is_child & is_not_disabled,
                    is_child & is_standard_disabled,
                    is_child & is_severely_disabled,
                ],
                [
                    gc.child.addition,
                    gc.child.addition + gc.child.disability.addition,
                    gc.child.addition + gc.child.disability.severe.addition,
                ],
            )
            * WEEKS_IN_YEAR
        )
        return benunit.sum(per_child_amount)
