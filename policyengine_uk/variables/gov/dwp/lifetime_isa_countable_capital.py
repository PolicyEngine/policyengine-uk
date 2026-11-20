from policyengine_uk.model_api import *
from policyengine_uk.utils.capital_valuation import lifetime_isa_surrender_value


class lifetime_isa_countable_capital(Variable):
    label = "Lifetime ISA value counted as means-tested capital"
    documentation = (
        "Surrender value of the person's Lifetime ISAs: the balance less the "
        "withdrawal charge below the charge-free age, and the whole balance "
        "from that age. Every means test values capital at its current market "
        "or surrender value, and DWP guidance counts a Lifetime ISA at 75% of "
        "its value under 60 and in full from 60. Not modelled: the "
        "charge-free withdrawals towards a first home or with a terminal "
        "illness."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/49",
        "https://assets.publishing.service.gov.uk/media/693ace15c72b0f8ccf33d609/adm-ch-H1.pdf#page=56",
        "https://www.legislation.gov.uk/uksi/1998/1870/schedule",
    ]

    # The shared function's identity lets the means tests distinguish this
    # baseline formula from a reform. They work it again in float64 before
    # rounding, while preserving explicit inputs and reformed values
    # (capital_valuation.valued_person_capital).
    formula = lifetime_isa_surrender_value
