from policyengine_uk.model_api import *


class housing_benefit_child_disability_premiums(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit child disability premiums"
    documentation = (
        "Disabled-child and enhanced-child premiums for legally dependent "
        "children and young persons. Uses actual DLA or PIP receipt, AFIP, "
        "and the existing blindness indicator; enhanced rates additionally "
        "require highest DLA care or enhanced PIP daily living receipt, or "
        "AFIP. Scottish replacement awards must be represented in the existing "
        "benefit fields: separate replacement-award fields are not available. "
        "Hospital suspension, blindness run-on and bereavement continuation "
        "are not reconstructed. A generic disability flag is insufficient. "
        "These child amounts are separate from the shared adult premiums."
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
            (dla_care & person("receives_highest_dla_sc", period))
            | (pip_daily & person("receives_enhanced_pip_dl", period))
            | afip
        )
        weekly = p.disabled_child * disabled + p.enhanced_disabled_child * enhanced
        return benunit.sum(child * weekly) * WEEKS_IN_YEAR
