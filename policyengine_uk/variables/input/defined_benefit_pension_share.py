from policyengine_uk.model_api import *


class defined_benefit_pension_share(Variable):
    value_type = float
    entity = Person
    label = "Share of workplace pension contributions paid into defined-benefit arrangements"
    documentation = (
        "The share, from 0 to 1, of the person's workplace pension "
        "contributions that is paid into defined-benefit arrangements: "
        "employer contributions, employee contributions under a net pay "
        "arrangement and salary sacrifice. Personal pension contributions "
        "(relief at source) are money purchase. The pension input amount of "
        "a defined-benefit arrangement is the increase in the value of the "
        "member's rights (FA 2004 s. 234), not the contributions paid, so the "
        "annual allowance counts defined_benefit_pension_input_amount in "
        "place of this share of the contributions. Data that records scheme "
        "type supplies it. The default of nil treats every contribution as "
        "money purchase."
    )
    definition_period = YEAR
    unit = "/1"
    reference = [
        dict(
            title="Finance Act 2004 s. 229 (total pension input amount)",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/229",
        ),
        dict(
            title="Finance Act 2004 s. 234 (defined benefits arrangements)",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/234",
        ),
    ]
