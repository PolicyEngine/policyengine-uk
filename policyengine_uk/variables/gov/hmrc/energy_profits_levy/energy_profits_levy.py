from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class energy_profits_levy(Variable):
    value_type = float
    entity = Firm
    label = "Energy profits levy"
    documentation = (
        "Energy profits levy on a company's levy profits (Energy (Oil and "
        "Gas) Profits Levy Act 2022), supplied as firm_epl_profits after the "
        "investment and decarbonisation allowances and levy loss relief: "
        "25% from 26 May 2022, 35% from 1 January 2023 and 38% from 1 "
        "November 2024, to 31 March 2030. The rate is day-weighted over 6 "
        "April to 5 April. Companies only. Not modelled: the allowances and "
        "levy loss relief (they are in the input), ring fence corporation "
        "tax and the supplementary charge, the energy security investment "
        "mechanism (price floor) and exact apportionment of straddling "
        "periods."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2022/40/section/1",
        "https://www.legislation.gov.uk/ukpga/2025/8/section/15",
        "https://www.legislation.gov.uk/ukpga/2025/8/section/17",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.energy_profits_levy
        return p.rate * max_(firm("firm_epl_profits", period), 0)
