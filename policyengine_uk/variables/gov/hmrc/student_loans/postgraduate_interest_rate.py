from policyengine_uk.model_api import *


class postgraduate_interest_rate(Variable):
    value_type = float
    entity = Person
    label = "Postgraduate loan interest rate"
    documentation = (
        "Interest rate for Postgraduate loans (Master's and Doctoral). "
        "Per Regulation 21B: 'RPI plus 3%'. "
        "Unlike Plan 2, this rate applies regardless of income."
    )
    definition_period = YEAR
    unit = "/1"
    reference = "https://www.legislation.gov.uk/uksi/2009/470/regulation/21B"

    def formula(person, period, parameters):
        p = parameters(period).gov
        # Per Regulation 21B: "RPI plus 3%"
        return (
            p.economic_assumptions.yoy_growth.obr.rpi
            + p.hmrc.student_loans.interest_rates.postgraduate_additional_rate
        )
