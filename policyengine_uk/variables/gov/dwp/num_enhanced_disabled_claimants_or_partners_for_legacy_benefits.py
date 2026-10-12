from policyengine_uk.model_api import *


class num_enhanced_disabled_claimants_or_partners_for_legacy_benefits(Variable):
    value_type = int
    entity = BenUnit
    label = "Enhanced-disabled claimants or partners for legacy benefits"
    documentation = (
        "Claimants and partners satisfying the model's existing "
        "is_enhanced_disabled_for_benefits indicator. This count excludes "
        "children and young persons, whose separate enhanced premium is "
        "not modelled here."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13A",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/15",
    )

    def formula(benunit, period, parameters):
        claimant_or_partner = benunit.members("is_claimant_or_partner", period)
        disabled = benunit.members("is_enhanced_disabled_for_benefits", period)
        return benunit.sum(claimant_or_partner & disabled)
