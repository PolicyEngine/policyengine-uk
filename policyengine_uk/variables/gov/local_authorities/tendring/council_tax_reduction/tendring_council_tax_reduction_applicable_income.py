from policyengine_uk.model_api import *


class tendring_council_tax_reduction_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Tendring Council Tax Reduction applicable income"
    documentation = "Tendring paragraphs 15.1 and 15.2 treat income and capital of household members other than dependent children as income and capital of the applicant. This sums each benefit unit's standard CTR applicable income once across the household, so non-dependants affect the taper through applicable income rather than through paragraph 58 non-dependant deductions, which are marked 'Not Used'."
    definition_period = YEAR
    unit = GBP
    reference = "https://legacy.tendringdc.gov.uk/sites/default/files/documents/Council_Tax/Tendring%20S13A%20202627%20Scheme%20Final.pdf"

    def formula(benunit, period, parameters):
        person = benunit.household.members
        is_benunit_head = person("is_benunit_head", period)
        applicable_income = person.benunit(
            "council_tax_reduction_applicable_income", period
        )
        return benunit.household.sum(is_benunit_head * applicable_income)
