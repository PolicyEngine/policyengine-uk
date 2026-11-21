from policyengine_uk.model_api import *


class firm_total_relevant_expenditure(Variable):
    value_type = float
    entity = Firm
    label = "Firm total relevant expenditure"
    documentation = "Total relevant expenditure in the year used as the denominator of the R&D intensity test: expenditure deducted in computing trading profits plus capitalised R&D, excluding payments to connected companies."
    definition_period = YEAR
    unit = GBP
