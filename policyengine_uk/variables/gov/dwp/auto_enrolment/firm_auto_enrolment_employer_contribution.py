from policyengine_uk.model_api import *


class firm_auto_enrolment_employer_contribution(Variable):
    value_type = float
    entity = Firm
    label = "Firm automatic enrolment employer minimum contribution"
    documentation = (
        "The employer's minimum contribution to a money purchase scheme used "
        "for automatic enrolment: the minimum rate times its employees' "
        "qualifying earnings (Pensions Act 2008 s.20(1)(b)). It is an "
        "employment cost, not a tax."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Pensions Act 2008 s.20(1)(b)",
            href="https://www.legislation.gov.uk/ukpga/2008/30/section/20",
        ),
        dict(
            title="Pensions Act 2008 s.29",
            href="https://www.legislation.gov.uk/ukpga/2008/30/section/29",
        ),
    ]

    def formula(firm, period, parameters):
        p = parameters(period).gov.dwp.auto_enrolment
        qualifying_earnings = firm("firm_auto_enrolment_qualifying_earnings", period)
        return p.employer_minimum_contribution_rate * qualifying_earnings
