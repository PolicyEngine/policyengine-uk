from policyengine_uk.model_api import *


class uc_statutory_payments_treated_as_employed_earnings(Variable):
    value_type = float
    entity = Person
    label = "Statutory payments treated as Universal Credit employed earnings"
    documentation = (
        "Statutory sick, maternity, paternity, adoption, shared parental, "
        "parental bereavement and neonatal care pay, which regulation 55(4) "
        "treats as employed earnings. Each counts from the date its "
        "sub-paragraph came into force."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="The Universal Credit Regulations 2013 reg. 55(4)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
    )
    adds = "gov.dwp.universal_credit.means_test.income_definitions.statutory_payments_treated_as_employed_earnings"
