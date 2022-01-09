from openfisca_uk.model_api import *


class ctc_disability_element(Variable):
    label = "CTC disability element"
    documentation = "Value of the disability element of the Child Tax Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/7"

    def formula(benunit, period):
        person = benunit.members
        amount_per_child = where(
            person("is_severely_disabled_for_benefits", period),
            person("ctc_severe_disability_element", period),
            person("ctc_standard_disability_element", period),
        )
        return benunit.sum(amount_per_child)

class ctc_standard_disability_element(Variable):
    label = "CTC standard disability element"
    documentation = "Value of the standard disability element of the Child Tax Credit"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/7"

    def formula(person, period, parameters):
        qualifies = person("is_disabled_for_benefits", period) & person("is_child_or_QYP", period)
        element = parameters(period).hmrc.tax_credits.child_tax_credit.elements.disability
        return element * qualifies


class ctc_severe_disability_element(Variable):
    label = "CTC severe disability element"
    documentation = "Value of the severe disability element of the Child Tax Credit"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/7"

    def formula(person, period, parameters):
        qualifies = person("is_severely_disabled_for_benefits", period) & person("is_child_or_QYP", period)
        element = parameters(period).hmrc.tax_credits.child_tax_credit.elements.severe_disability
        return element * qualifies
