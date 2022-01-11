from openfisca_uk.model_api import *


class wtc_couple_element(Variable):
    label = "WTC couple element"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2005/part/2/crossheading/second-adult-element"

    def formula(benunit, period, parameters):
        wtc = parameters(period).hmrc.tax_credits.working_tax_credit
        return wtc.elements.couple * benunit("is_joint_benunit", period)
