from policyengine_uk.model_api import *


class uc_LCWRA_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit limited capability for work-related-activity element"
    documentation = (
        "The amount an award includes because a claimant has limited "
        "capability for work and work-related activity. Only a claimant's "
        "limited capability counts: a disabled child or qualifying young "
        "person gives the award the disabled child addition instead "
        "(`uc_individual_disabled_child_element`). Joint claimants who both "
        "have limited capability have one element."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Welfare Reform Act 2012 s. 12(2)(b)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/12",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 27(1) and (4)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/27",
        ),
    ]

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.disabled
        person = benunit.members
        # Reg. 27(1): the element is "in respect of the fact that a claimant
        # has limited capability for work and work-related activity".
        claimant = person("is_uc_assessed_claimant", period)
        limited_capability = claimant & person("uc_limited_capability_for_WRA", period)
        # Reg. 27(4)(a): "In the case of joint claimants, where each of them
        # has limited capability for work and work-related activity, the
        # award is only to include one LCWRA element".
        return benunit.any(limited_capability) * p.amount * MONTHS_IN_YEAR
