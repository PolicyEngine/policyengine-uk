from policyengine_uk.model_api import *


class salary_sacrifice_pension_ni_employer(Variable):
    label = "Employer NI on salary sacrifice pension contributions above cap"
    documentation = (
        "Additional employer National Insurance contributions due to "
        "salary sacrifice pension contributions exceeding the cap. "
        "The excess remains an employer pension contribution and is included "
        "only in NIC earnings. This reporting measure is separate from "
        "the actual Class 1 contribution curve and liability flags."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://policyengine.org/uk/research/uk-salary-sacrifice-cap"

    def formula(person, period, parameters):
        # NIC-only earnings; this does not become an actual member payment.
        excess = person("salary_sacrifice_pension_ni_excess", period)

        # Use existing NI Class 1 employer rate parameter
        ni_params = parameters(period).gov.hmrc.national_insurance.class_1
        employer_rate = ni_params.employer_scale.components[1].rate

        return excess * employer_rate
