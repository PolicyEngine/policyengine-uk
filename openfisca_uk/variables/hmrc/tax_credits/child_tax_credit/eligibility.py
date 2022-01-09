from openfisca_uk.model_api import *
from openfisca_core.parameters import ParameterAtInstant
from openfisca_core.periods.helpers import instant


class is_child_for_CTC(Variable):
    value_type = bool
    entity = Person
    label = "Child eligible for Child Tax Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/5"

    def formula(person, period):
        return person("is_child_or_QYP", period)


class meets_ctc_child_limit(Variable):
    value_type = bool
    entity = Person
    label = "Meets the CTC child limit"
    documentation = "Whether this person is not disqualified for the Child Tax Credit by the child limit"
    definition_period = YEAR

    def formula(person, period, parameters):
        limit = parameters.hmrc.child_tax_credit.eligibility.child_limit
        limit_when_born = np.array([limit(birth_date) for birth_date in person("birth_date", period)])
        return person("child_index", period) <= limit_when_born


class CTC_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Child Tax Credit child element"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/contents"
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        person = benunit.members
        CTC = parameters(period).benefit.tax_credits.child_tax_credit
        is_child_for_CTC = (
            person("is_child_for_CTC", period)
            & person("meets_ctc_child_limit", period)
        )
        eligible_children = benunit.sum(is_child_for_CTC)
        amount = CTC.elements.child_element * eligible_children
        return amount * benunit("claims_CTC", period)