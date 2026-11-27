from policyengine_uk.model_api import *


class firm_prior_year_secondary_class_1_liabilities(Variable):
    value_type = float
    entity = Firm
    label = "Firm secondary Class 1 liabilities in the previous tax year"
    documentation = (
        "Qualifying secondary Class 1 National Insurance liabilities of the "
        "firm and its connected companies or charities for the previous tax "
        "year, before the Employment Allowance. From 2020-21 to 2024-25 an "
        "employer with £100,000 or more could not claim the allowance. "
        "Supply it as an input where known. Otherwise the formula takes the "
        "firm's own liabilities for the current year, which ignores growth "
        "between years and the liabilities of connected companies."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="National Insurance Contributions Act 2014 s.2(4B)-(4E), as at 6 April 2020",
            href="https://www.legislation.gov.uk/ukpga/2014/7/section/2/2020-04-06",
        ),
    ]

    def formula(firm, period, parameters):
        return firm("firm_employer_ni_before_allowance", period)
