from policyengine_uk.model_api import *


class meets_uc_higher_disabled_child_condition(Variable):
    value_type = bool
    entity = Person
    label = "Meets the Universal Credit higher disabled child condition"
    definition_period = YEAR
    documentation = (
        "The higher UC disabled child condition has an independent certified "
        "blindness limb and qualifying DLA care or PIP daily living awards. "
        "The model reads DLA and PIP amounts, computed from their categories "
        "unless an amount is supplied directly. It retains the existing "
        "nonstatutory weekly amount tolerance for those paid-amount proxies; "
        "they do not establish underlying entitlement from partial payments. "
        "Separate Scottish awards and benefit payable but for a hospital "
        "stay are not represented. The child amount separately checks "
        "dependent child or qualifying young person status and excludes "
        "the UC claimant. The shared tax-credit severe disability flag, "
        "attendance allowance and AFIP do not establish this UC condition."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/24",
        "https://www.legislation.gov.uk/uksi/2016/216/regulation/25",
    )

    def formula(person, period, parameters):
        dwp = parameters(period).gov.dwp
        tolerance = (
            dwp.universal_credit.elements.child.severely_disabled.benefit_amount_tolerance
            * WEEKS_IN_YEAR
        )
        highest_dla_care = (
            person("dla_sc", period)
            >= dwp.dla.self_care.higher * WEEKS_IN_YEAR - tolerance
        )
        enhanced_pip_daily_living = (
            person("pip_dl", period)
            >= dwp.pip.daily_living.enhanced * WEEKS_IN_YEAR - tolerance
        )
        return person("is_blind", period) | highest_dla_care | enhanced_pip_daily_living
