from policyengine_uk.model_api import *


class firm_off_payroll_deemed_workers(Variable):
    value_type = int
    entity = Firm
    label = "Firm off-payroll deemed workers"
    documentation = "Number of workers whose deemed direct payments make up firm_off_payroll_deemed_payments. The secondary threshold is deducted once for each. At the default of 0, firm_off_payroll_deemed_payments is treated as already above the threshold."
    definition_period = YEAR
    hidden_input = True
    unit = "person"
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/9"
