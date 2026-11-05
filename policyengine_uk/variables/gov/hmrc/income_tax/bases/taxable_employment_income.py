from policyengine_uk.model_api import *


class taxable_employment_income(Variable):
    value_type = float
    entity = Person
    label = "Net taxable earnings"
    definition_period = YEAR
    reference = dict(
        title="Income Tax (Earnings and Pensions) Act 2003, s. 11",
        href="https://www.legislation.gov.uk/ukpga/2003/1/section/11",
    )
    unit = GBP

    def formula(person, period, parameters):
        taxable_earnings = person("employment_income", period)
        deductions = add(person, period, ["employment_deductions"])
        benefits = person("employment_benefits", period)
        # Benefits code earnings (ITEPA 2003 s. 63), held apart from pay and
        # statutory pay because Class 1 NICs and the means tests' earnings
        # leave them out.
        benefits_in_kind = person("benefits_in_kind", period)
        return max_(0, taxable_earnings + benefits + benefits_in_kind - deductions)
