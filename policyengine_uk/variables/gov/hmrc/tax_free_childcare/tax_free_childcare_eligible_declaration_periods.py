from policyengine_uk.model_api import *


class tax_free_childcare_eligible_declaration_periods(Variable):
    value_type = int
    entity = BenUnit
    label = "Tax-Free Childcare eligible declaration periods"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2015/448/regulation/9"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.hmrc.tax_free_childcare
        eligible = benunit("tax_free_childcare_eligible", period)
        return eligible * p.declaration_periods_per_year
