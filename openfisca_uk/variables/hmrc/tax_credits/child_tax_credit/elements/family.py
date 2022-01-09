from openfisca_uk.model_api import *
from openfisca_core.periods.helpers import instant


class ctc_family_element(Variable):
    label = "Family element"
    documentation = "Value of the family element of the Child Tax Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/7"

    def formula(benunit, period, parameters):
        active_at_date = lambda date: parameters(date).hmrc.tax_credits.child_tax_credit.elements.family.active
        amount = parameters(period).hmrc.tax_credits.child_tax_credit.elements.family.amount
        person = benunit.members
        payable_at_birth = np.array([
            active_at_date(instant(birth_date))
            for birth_date in person("birth_date", period).astype(date)
        ])
        element_is_payable = benunit.max(person("is_child_for_ctc", period) * payable_at_birth)
        eligible = benunit("is_ctc_eligible", period)
        return amount * element_is_payable * eligible
