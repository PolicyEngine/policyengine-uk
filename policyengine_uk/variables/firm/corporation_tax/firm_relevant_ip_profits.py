from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_relevant_ip_profits(Variable):
    value_type = float
    entity = Firm
    label = "Firm relevant IP profits"
    documentation = (
        "Relevant IP profits of a company that has elected into the Patent "
        "Box (CTA 2010 Part 8A), after streaming and the nexus fraction, "
        "which firm data cannot reproduce. Defaults to 0, so no Patent Box "
        "deduction is made."
    )
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/357A"
