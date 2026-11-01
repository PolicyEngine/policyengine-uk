from policyengine_uk.model_api import *


class has_highest_dla_sc_award(Variable):
    label = "Has an award of the DLA care component at the highest rate"
    documentation = (
        "Whether the person has an award of the care component of disability "
        "living allowance at the highest rate. An award needs a positive "
        "amount (dla_sc), so an amount of zero, including one a reform sets "
        "by neutralising dla_sc, is no award. The rate comes from the award "
        "category (dla_sc_category) or from the amount: an amount entered "
        "without its category counts when it reaches the highest weekly rate "
        "less a tolerance (gov.dwp.disability_premia.top_rate_amount_"
        "tolerance), times 52. The Regulations also count an award whose "
        "payment stops while the person is in hospital; the model has no input "
        "for that."
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
        amount = person("dla_sc", period)
        threshold = (
            p.dla.self_care.higher - p.disability_premia.top_rate_amount_tolerance
        ) * WEEKS_IN_YEAR
        highest_rate = person("receives_highest_dla_sc", period) | (amount >= threshold)
        return (amount > 0) & highest_rate
