from policyengine_uk.model_api import *


class esa_includes_support_component(Variable):
    value_type = bool
    entity = Person
    label = "ESA includes the support component"
    documentation = (
        "Whether this person's employment and support allowance includes the "
        "support component: the assessment phase has ended and they have "
        "limited capability for work-related activity (Welfare Reform Act 2007 "
        "s.2(2) for the contributory allowance, s.4(4) for the income-related "
        "allowance). Surveys record this as being in the ESA support group. "
        "Datasets or users can supply it. Otherwise it is assumed for anyone "
        "with an ESA award of their own (has_own_esa_award): in the Family "
        "Resources Survey 2024-25 about nine in ten ESA recipients who answer "
        "say they are in the support group."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2007/5/section/2",
        "https://www.legislation.gov.uk/ukpga/2007/5/section/4",
    )

    def formula(person, period, parameters):
        return person("has_own_esa_award", period)
