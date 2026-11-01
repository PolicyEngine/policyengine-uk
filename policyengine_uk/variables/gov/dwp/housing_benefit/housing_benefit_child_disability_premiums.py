from policyengine_uk.model_api import *


class housing_benefit_child_disability_premiums(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit child disability premiums"
    documentation = (
        "Disabled-child and enhanced-child premiums for legally dependent "
        "children and young persons. The disabled-child rate needs a positive "
        "DLA or PIP amount (either component), AFIP or the blindness "
        "indicator. The enhanced rate needs an award that meets the adult "
        "condition: the highest DLA care rate (has_highest_dla_sc_award), the "
        "enhanced PIP daily living rate (has_enhanced_pip_dl_award) or AFIP. "
        "The model has no separate fields for Scottish replacement awards, so "
        "callers enter them in the DLA and PIP fields. The model omits "
        "hospital suspension, the blindness run-on and bereavement "
        "continuation, and a generic disability flag does not qualify. These "
        "child amounts are separate from the shared adult premiums."
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
        dla_care = person("dla_sc", period) > 0
        dla = dla_care | (person("dla_m", period) > 0)
        pip_daily = person("pip_dl", period) > 0
        pip = pip_daily | (person("pip_m", period) > 0)
        afip = person("armed_forces_independence_payment", period) > 0
        disabled = dla | pip | afip | person("is_blind", period)
        enhanced = (
            person("has_highest_dla_sc_award", period)
            | person("has_enhanced_pip_dl_award", period)
            | afip
        )
        weekly = p.disabled_child * disabled + p.enhanced_disabled_child * enhanced
        return benunit.sum(child * weekly) * WEEKS_IN_YEAR
