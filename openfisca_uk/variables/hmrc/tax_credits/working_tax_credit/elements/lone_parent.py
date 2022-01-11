from openfisca_uk.model_api import *


class wtc_lone_parent_element(Variable):
    label = "WTC lone parent element"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2005/part/2/crossheading/lone-parent-element"

    def formula(benunit, period, parameters):
        wtc = parameters(period).hmrc.tax_credits.working_tax_credit
        return wtc.elements.lone_parent * benunit("is_lone_parent", period)
