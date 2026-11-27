from policyengine_uk.model_api import *


class firm_termination_awards(Variable):
    value_type = float
    entity = Firm
    label = "Firm termination awards"
    documentation = "Termination awards the firm pays that count as employment income under ITEPA 2003 s.403, before the £30,000 threshold, aggregated for each employee. Leave out amounts charged to Class 1, such as post-employment notice pay (s.402B). Defaults to 0."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/1/section/403"
