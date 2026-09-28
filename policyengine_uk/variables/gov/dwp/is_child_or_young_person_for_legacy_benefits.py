from policyengine_uk.model_api import *


class is_child_or_young_person_for_legacy_benefits(Variable):
    """Child or young person in the family for the legacy means-tested schemes.

    Income Support, income-based Jobseeker's Allowance, income-related
    Employment and Support Allowance, Housing Benefit and council tax
    reduction schemes define a child as a person under 16 (SSCBA 1992
    s.137(1)) and a young person as a Child Benefit qualifying young person
    (SSCBA 1992 s.142), excluding young persons entitled to a benefit in
    their own right. That is the Child Benefit child or qualifying young
    person test, restricted to members who are not the claimant or partner.
    """

    value_type = bool
    entity = Person
    label = "Child or young person for legacy means-tested benefits"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/137",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/14",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/19",
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/76",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
    )

    def formula(person, period, parameters):
        return person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        ) & ~person("is_claimant_or_partner", period)
