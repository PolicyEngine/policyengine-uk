from policyengine_uk.model_api import *


class extended_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligibility for extended childcare entitlement"
    definition_period = YEAR
    defined_for = "would_claim_extended_childcare"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2016/5/section/1",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/14",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/15",
    )

    def formula(benunit, period, parameters):
        # Check if household is in England
        country = benunit.household("country", period)
        countries = country.possible_values
        in_england = country == countries.ENGLAND

        # The income conditions apply to the parent and the parent's partner
        # (Childcare Act 2016 s.1(2)(d); SI 2022/1134 regs 14, 15 and 18):
        # the claimant and partner of the benefit unit, not their children.
        person = benunit.members
        person_meets_income_condition = person(
            "extended_childcare_entitlement_meets_income_requirements",
            period,
        ) | ~person("is_claimant_or_partner", period)
        meets_income_condition = benunit.all(person_meets_income_condition)

        # Check work condition
        work_eligible = (
            benunit("extended_childcare_entitlement_work_condition", period) > 0
        )

        return in_england & meets_income_condition & work_eligible
