from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    ALL_REQUIREMENTS,
    INTERVIEW_ONLY,
    NO_REQUIREMENTS,
    WORK_PREPARATION,
    work_related_group,
)


class UCWorkRelatedGroup(Enum):
    NO_REQUIREMENTS = "No work-related requirements"
    INTERVIEW_ONLY = "Work-focused interview requirement only"
    WORK_PREPARATION = "Work preparation requirement"
    ALL_REQUIREMENTS = "All work-related requirements"
    NOT_A_CLAIMANT = "Not a claimant"


class uc_work_related_group_apart_from_earnings(Variable):
    value_type = Enum
    possible_values = UCWorkRelatedGroup
    default_value = UCWorkRelatedGroup.NOT_A_CLAIMANT
    entity = Person
    label = "Universal Credit work-related group, apart from the earnings thresholds"
    documentation = (
        "The work-related group the claimant would fall within apart from "
        "regulations 62 and 90 of the Universal Credit Regulations 2013: "
        "before asking whether their earnings reach their threshold, or "
        "whether the minimum income floor treats them as having such "
        "earnings, either of which would put them in the group subject to no "
        "work-related requirements. This is the test for the minimum income "
        "floor (reg. 62(1)(b)) and for each claimant's individual threshold "
        "(reg. 90(2))."
    )
    reference = [
        dict(
            title="Welfare Reform Act 2012 ss. 19 to 22",
            href="https://www.legislation.gov.uk/ukpga/2012/5/part/1/chapter/2/crossheading/application-of-workrelated-requirements",
        ),
        dict(
            title="Universal Credit Regulations 2013 regs. 89 and 91",
            href="https://www.legislation.gov.uk/uksi/2013/376/part/8/chapter/1/crossheading/workrelated-groups",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 62(1)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/62",
        ),
    ]
    definition_period = YEAR

    def formula(person, period, parameters):
        group = work_related_group(
            person, period, parameters, person("uc_is_responsible_carer", period)
        )
        return select(
            [
                group == NO_REQUIREMENTS,
                group == INTERVIEW_ONLY,
                group == WORK_PREPARATION,
                group == ALL_REQUIREMENTS,
            ],
            [
                UCWorkRelatedGroup.NO_REQUIREMENTS,
                UCWorkRelatedGroup.INTERVIEW_ONLY,
                UCWorkRelatedGroup.WORK_PREPARATION,
                UCWorkRelatedGroup.ALL_REQUIREMENTS,
            ],
            default=UCWorkRelatedGroup.NOT_A_CLAIMANT,
        )
