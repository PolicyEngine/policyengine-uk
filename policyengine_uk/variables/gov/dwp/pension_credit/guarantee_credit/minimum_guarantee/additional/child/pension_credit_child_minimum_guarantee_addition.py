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
        gc = parameters(period).gov.dwp.pension_credit.guarantee_credit.child

        base_amount = benunit.sum(is_child) * gc.amount * WEEKS_IN_YEAR
        disabled_child_amount = benunit("pension_credit_disabled_child_minimum_guarantee_addition", period)
        return base_amount + disabled_child_amount
