from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit._child_disability_premiums import (
    child_disability_premium_benefit_conditions,
)


class housing_benefit_child_disability_premiums(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit child disability premiums"
    documentation = (
        "The model pays the disabled-child and enhanced-child premiums for "
        "legally dependent children and young persons. A child qualifies for "
        "the disabled-child rate through a positive DLA or PIP amount (either "
        "component), AFIP or the blindness indicator, and for the enhanced "
        "rate through an award that meets the adult condition: the highest "
        "DLA care rate (has_highest_dla_sc_award), the enhanced PIP daily "
        "living rate (has_enhanced_pip_dl_award) or AFIP. The model has no "
        "separate fields for Scottish replacement awards, so callers enter "
        "them in the DLA and PIP fields. The model omits hospital suspension, "
        "the blindness run-on and bereavement continuation, and a generic "
        "disability flag does not qualify. The model computes these child "
        "premiums separately from the adult premiums."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/15",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/16",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/7",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/8",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4/paragraph/15",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4/paragraph/16",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/4/paragraph/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/4/paragraph/8",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.premiums
        person = benunit.members
        child = person("is_child_or_young_person_for_legacy_benefits", period)
        disabled, enhanced = child_disability_premium_benefit_conditions(person, period)
        # Housing Benefit counts AFIP for any child or young person in both
        # premiums.
        afip = person("armed_forces_independence_payment", period) > 0
        disabled = disabled | afip
        enhanced = enhanced | afip
        weekly = p.disabled_child * disabled + p.enhanced_disabled_child * enhanced
        return benunit.sum(child * weekly) * WEEKS_IN_YEAR
