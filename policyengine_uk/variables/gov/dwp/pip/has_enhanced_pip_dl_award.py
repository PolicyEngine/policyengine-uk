from policyengine_uk.model_api import *


class has_enhanced_pip_dl_award(Variable):
    label = "Has an award of the PIP daily living component at the enhanced rate"
    documentation = (
        "Whether the person has an award of the daily living component of "
        "personal independence payment at the enhanced rate. An award needs a "
        "positive amount (pip_dl), so an amount of zero, including one a "
        "reform sets by neutralising pip_dl, is no award. The rate comes from "
        "the award category (pip_dl_category) or from the amount: an amount "
        "entered without its category counts when it reaches the enhanced "
        "weekly rate less a tolerance (gov.dwp.disability_premia.top_rate_"
        "amount_tolerance), times 52. The Regulations also count an award "
        "whose payment stops while the person is in hospital; the model has no "
        "input for that."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/15",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13A",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp
        amount = person("pip_dl", period)
        threshold = (
            p.pip.daily_living.enhanced - p.disability_premia.top_rate_amount_tolerance
        ) * WEEKS_IN_YEAR
        enhanced_rate = person("receives_enhanced_pip_dl", period) | (
            amount >= threshold
        )
        return (amount > 0) & enhanced_rate
