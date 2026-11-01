from policyengine_uk.model_api import *


class has_highest_dla_sc_award(Variable):
    label = "Has an award of the DLA care component at the highest rate"
    documentation = (
        "The model counts an award of the care component of disability "
        "living allowance at the highest rate when the person has a positive "
        "amount (dla_sc) and either the highest-rate category "
        "(dla_sc_category) or an amount that reaches 52 × (highest weekly "
        "rate − weekly tolerance; gov.dwp.disability_premia.top_rate_"
        "amount_tolerance). It rejects an amount of zero, including one that "
        "a reform sets by neutralising dla_sc. Claimants also qualify while "
        "the suspension or hospital rules stop or abate payment of the award "
        "(HB Regs 2006 Sch 3 para 15(1)(b)); the model has no input for that."
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
