from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_liable_to_corporation_tax(Variable):
    value_type = bool
    entity = Firm
    label = "firm is liable to corporation tax"
    documentation = (
        "Companies pay corporation tax. Sole traders and partnerships pay "
        "income tax on their profits instead."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/2"

    def formula(firm, period, parameters):
        legal_form = firm("firm_legal_form", period)
        return legal_form == legal_form.possible_values.COMPANY
