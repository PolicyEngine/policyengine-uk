from policyengine_uk.model_api import *


class lifetime_isa_countable_capital(Variable):
    label = "Lifetime ISA value counted as means-tested capital"
    documentation = (
        "Surrender value of the person's Lifetime ISAs: the balance less the "
        "withdrawal charge below the charge-free age, and the whole balance "
        "from that age. Every means test values capital at its current market "
        "or surrender value, and DWP guidance counts a Lifetime ISA at 75% of "
        "its value under 60 and in full from 60. Qualifying written medical "
        "evidence received by the account manager also removes the charge. "
        "Evidence is assessed at the annual age date, 6 October. Prospective "
        "first-home eligibility does not remove the charge from unrestricted "
        "surrender: the purchase exception requires a qualifying transaction "
        "and direct payment to a conveyancer."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/49",
        "https://assets.publishing.service.gov.uk/media/693ace15c72b0f8ccf33d609/adm-ch-H1.pdf#page=56",
        "https://www.legislation.gov.uk/uksi/1998/1870/schedule",
        "https://www.legislation.gov.uk/uksi/1998/1870/schedule/paragraph/4",
        "https://www.legislation.gov.uk/uksi/1998/1870/schedule/paragraph/6",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.isa.lifetime
        balance = person("lifetime_isa_balance", period)
        charge_free = person("age", period) >= p.charge_free_age
        medical = person("lifetime_isa_qualifying_medical_evidence", period) & (
            person("lifetime_isa_medical_evidence_received_date", period)
            <= np.datetime64(f"{period.start.year}-10-06")
        )
        charge_free = charge_free | medical
        return where(charge_free, balance, balance * (1 - p.withdrawal_charge))
