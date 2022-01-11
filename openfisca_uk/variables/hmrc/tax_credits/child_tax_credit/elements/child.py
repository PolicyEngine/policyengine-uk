from openfisca_uk.model_api import *
from openfisca_core.periods.helpers import instant


class is_ctc_child_limit_exempt(Variable):
    label = "Is exempt from the CTC child limit"
    documentation = (
        "Whether this benefit unit is exempt from the CTC child limit"
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/9"


class meets_ctc_child_limit(Variable):
    value_type = bool
    entity = Person
    label = "Meets the child limit"
    documentation = "Whether this person is not disqualified for the Child Tax Credit by the child limit"
    definition_period = YEAR

    def formula(person, period, parameters):
        def limit_at_date(date):
            return parameters(
                date
            ).hmrc.tax_credits.child_tax_credit.eligibility.child_limit

        limit_when_born = np.array(
            [
                limit_at_date(instant(birth_date))
                for birth_date in person("birth_date", period).astype(date)
            ]
        )
        return person("child_index", period) <= limit_when_born


class ctc_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Child element"
    documentation = "Value of the per-child element of the Child Tax Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/7"
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        person = benunit.members
        CTC = parameters(period).benefit.tax_credits.child_tax_credit
        exempt_from_limit = benunit.project(
            benunit("is_ctc_child_limit_exempt", period)
        )
        is_child_for_ctc = person("is_child_for_ctc", period) & (
            person("meets_ctc_child_limit", period) | exempt_from_limit
        )
        eligible_children = benunit.sum(is_child_for_ctc)
        amount = CTC.elements.child_element * eligible_children
        return amount
