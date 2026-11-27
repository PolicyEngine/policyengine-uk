from policyengine_uk.model_api import *


class firm_termination_award_recipients(Variable):
    value_type = int
    entity = Firm
    label = "Firm termination award recipients"
    documentation = "Number of employees whose awards make up firm_termination_awards. The £30,000 threshold is deducted once for each. At the default of 0, firm_termination_awards is treated as already above the threshold."
    definition_period = YEAR
    hidden_input = True
    unit = "person"
    reference = "https://www.legislation.gov.uk/ukpga/2003/1/section/403"
