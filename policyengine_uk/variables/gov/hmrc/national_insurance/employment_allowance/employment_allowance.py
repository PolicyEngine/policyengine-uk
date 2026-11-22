from policyengine_uk.model_api import *


class employment_allowance(Variable):
    value_type = float
    entity = Firm
    label = "Employment Allowance"
    documentation = (
        "Reduction in the firm's secondary Class 1 contributions for the "
        "tax year: the maximum allowance or, if less, the firm's secondary "
        "Class 1 liabilities."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "employment_allowance_eligible"
    reference = [
        dict(
            title="National Insurance Contributions Act 2014 s.1",
            href="https://www.legislation.gov.uk/ukpga/2014/7/section/1",
        ),
    ]

    def formula(firm, period, parameters):
        # Keep in step with
        # policyengine_uk/variables/contrib/policyengine/firm/firm_tax_change_total.py
        # (_employment_allowance_under_rules).
        p = parameters(period).gov.hmrc.national_insurance.employment_allowance
        liabilities = firm("firm_employer_ni_before_allowance", period)
        return min_(p.amount, liabilities)
