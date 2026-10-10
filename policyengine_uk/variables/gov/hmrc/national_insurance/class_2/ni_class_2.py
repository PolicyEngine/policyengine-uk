from policyengine_uk.model_api import *
from policyengine_uk.utils.class_2 import class_2_contribution_weeks, class_2_liable


class ni_class_2(Variable):
    value_type = float
    entity = Person
    label = "NI Class 2 contributions"
    documentation = (
        "Compulsory Class 2 contributions under s.11(2) SSCBA 1992 for a full "
        "year of self-employment: the weekly rate for each contribution week "
        "in the tax year (53 in 2019-20, otherwise 52 to 2023-24). Liability "
        "is tested on relevant profits, the profits on which Class 4 is "
        "payable under s.15 (s.11(3)), as modelled in ni_class_4_profits."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "ni_liable"
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992, s. 11",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/11",
        ),
        dict(
            title="HMRC National Insurance Manual NIM70650",
            href="https://www.gov.uk/hmrc-internal-manuals/national-insurance-manual/nim70650",
        ),
        dict(
            title="HMRC National Insurance Manual NIM70200",
            href="https://www.gov.uk/hmrc-internal-manuals/national-insurance-manual/nim70200",
        ),
    ]

    def formula(person, period, parameters):
        class_2 = parameters(period).gov.hmrc.national_insurance.class_2
        # Section 11(3) SSCBA 1992: "relevant profits" are the profits in
        # respect of which Class 4 is payable under s.15 (or would be, if they
        # exceeded the lower profits limit), which s.15(3) computes under
        # Schedule 2. Class 2 and Class 4 therefore share one profit base.
        profits = person("ni_class_4_profits", period)
        # The flat rate is 0 once s.11(2) is omitted in 2024-25.
        weeks = class_2_contribution_weeks(period.start.year)
        return class_2_liable(profits, class_2) * class_2.flat_rate * weeks
