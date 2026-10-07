from policyengine_uk.model_api import *


class ni_class_2(Variable):
    value_type = float
    entity = Person
    label = "NI Class 2 contributions"
    documentation = (
        "Compulsory Class 2 contributions under s.11(2) SSCBA 1992, tested on "
        "the earner's relevant profits: the profits on which Class 4 is "
        "payable under s.15 (s.11(3)), so after capital allowances, the "
        "trading allowance and Schedule 2 loss relief (ni_class_4_profits)."
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
            title="HMRC National Insurance Manual NIM70300",
            href="https://www.gov.uk/hmrc-internal-manuals/national-insurance-manual/nim70300",
        ),
    ]

    def formula(person, period, parameters):
        class_2 = parameters(period).gov.hmrc.national_insurance.class_2
        # Section 11(3) SSCBA 1992: "relevant profits" are the profits in
        # respect of which Class 4 is payable under s.15 (or would be, if they
        # exceeded the lower profits limit), which s.15(3) computes under
        # Schedule 2. Class 2 and Class 4 therefore share one profit base.
        profits = person("ni_class_4_profits", period)
        # Section 11(2). From 2022-23 only profits that exceed the lower
        # profits threshold are liable; profits from the small profits
        # threshold up to it are treated as paid (s.11(5A)-(5B)) and cost
        # nothing. Before then liability started at the small profits
        # threshold. The flat rate is 0 once s.11(2) is omitted in 2024-25.
        liable = where(
            class_2.lower_profits_threshold_applies,
            profits > class_2.lower_profits_threshold,
            profits >= class_2.small_profits_threshold,
        )
        return liable * class_2.flat_rate * WEEKS_IN_YEAR
