from policyengine_uk.model_api import *


class uc_carer_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit carer element"
    documentation = (
        "The amount an award includes because a claimant has regular and "
        "substantial caring responsibilities for a severely disabled person: "
        "the reg. 36 amount for each claimant in respect of whom the element "
        "is included (`uc_carer_element_included_for_claimant`)."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Welfare Reform Act 2012 s. 12(2)(c)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/12",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 29",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/29",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 36(3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/36",
        ),
    ]

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.carer
        elements = add(benunit, period, ["uc_carer_element_included_for_claimant"])
        return elements * p.amount * MONTHS_IN_YEAR
