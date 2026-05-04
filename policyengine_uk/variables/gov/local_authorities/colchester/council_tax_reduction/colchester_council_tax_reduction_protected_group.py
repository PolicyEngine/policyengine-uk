from policyengine_uk.model_api import *


class colchester_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Colchester CTR protected group"
    definition_period = YEAR
    reference = "https://cbccrmdata.blob.core.windows.net/noteattachment/CBC-null-Local-council-tax-support-policy-updated-01-04-26-Local%20Council%20Tax%20support%20policy.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        modeled_protected = (
            person("receives_enhanced_pip_dl", period)
            | person("receives_highest_dla_sc", period)
            | (person("armed_forces_independence_payment", period) > 0)
            | person("is_blind", period)
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        source_protected = benunit(
            "colchester_council_tax_reduction_source_protected_group", period
        )
        return (
            benunit.any(claimant_or_partner & modeled_protected)
            | relevant_income_based_benefit
            | source_protected
        )
