from policyengine_uk.model_api import *


class firm_rd_intensity(Variable):
    value_type = float
    entity = Firm
    label = "Firm R&D intensity"
    documentation = (
        "Qualifying research and development expenditure as a share of total "
        "relevant expenditure. Zero where relevant expenditure is zero."
    )
    definition_period = YEAR
    unit = "/1"
    reference = "https://www.legislation.gov.uk/ukpga/2009/4/part/13/chapter/2"

    def formula(firm, period, parameters):
        rd = firm("firm_qualifying_rd_expenditure", period)
        total = firm("firm_total_relevant_expenditure", period)
        return np.divide(rd, total, out=np.zeros_like(rd), where=total > 0)
