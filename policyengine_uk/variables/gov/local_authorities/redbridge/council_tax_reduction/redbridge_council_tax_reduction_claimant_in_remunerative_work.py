from policyengine_uk.model_api import *


class redbridge_council_tax_reduction_claimant_in_remunerative_work(Variable):
    value_type = bool
    entity = BenUnit
    label = "Redbridge Council Tax Reduction claimant in remunerative work"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        paid_work = (
            person("employment_income", period)
            + person("self_employment_income", period)
            + person("statutory_sick_pay", period)
            + person("statutory_maternity_pay", period)
            + person("statutory_paternity_pay", period)
        )
        return benunit.any(claimant_or_partner & (paid_work > 0))
