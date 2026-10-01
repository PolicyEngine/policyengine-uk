from policyengine_uk.model_api import *


class uc_carer_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit carer element"
    documentation = (
        "The amount an award includes because a claimant has regular and "
        "substantial caring responsibilities for a severely disabled person. "
        "Only a claimant's caring counts: a child or qualifying young person "
        "who is a carer does not give the claimants the element."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Welfare Reform Act 2012 s. 12(2)(c)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/12",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 29(1)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/29",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 30",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/30",
        ),
    ]

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.carer
        person = benunit.members
        # Reg. 29(1): the element is included "where a claimant has regular
        # and substantial caring responsibilities for a severely disabled
        # person" (reg. 30: `is_carer_for_benefits`).
        claimant = person("is_uc_assessed_claimant", period)
        carer = claimant & person("is_carer_for_benefits", period)
        return benunit.any(carer) * p.amount * MONTHS_IN_YEAR
