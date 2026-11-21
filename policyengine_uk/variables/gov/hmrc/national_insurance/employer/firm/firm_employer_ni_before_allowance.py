from policyengine_uk.model_api import *


class firm_employer_ni_before_allowance(Variable):
    value_type = float
    entity = Firm
    label = "Firm employer National Insurance before the Employment Allowance"
    documentation = (
        "Secondary Class 1 contributions on the firm's employees: the "
        "secondary percentage on earnings above the secondary threshold, "
        "less the earnings zero-rated for earners under 21, relevant "
        "apprentices under 25 and freeport or investment zone employees, "
        "before the Employment Allowance. Computed at firm level from "
        "aggregate earnings, as the model has no links between firms and "
        "the people they employ."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.9",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/9",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.9A",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/9A",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.9B",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/9B",
        ),
        dict(
            title="National Insurance Contributions Act 2022 s.1",
            href="https://www.legislation.gov.uk/ukpga/2022/9/section/1",
        ),
    ]

    def formula(firm, period, parameters):
        class_1 = parameters(period).gov.hmrc.national_insurance.class_1
        rate = class_1.employer_scale.components[1].rate
        above_threshold = firm(
            "firm_class_1_earnings_above_secondary_threshold", period
        )
        zero_rated = firm("firm_zero_rated_class_1_earnings", period)
        return rate * max_(above_threshold - zero_rated, 0)
