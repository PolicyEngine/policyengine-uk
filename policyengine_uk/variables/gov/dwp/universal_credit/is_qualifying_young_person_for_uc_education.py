from policyengine_uk.model_api import *

# Universal Credit (Transitional Provisions) Regulations 2014 reg. 2(1).
EXISTING_BENEFITS = [
    "jsa_income_reported",
    "esa_income_reported",
    "income_support_reported",
    "housing_benefit_reported",
    "child_tax_credit_reported",
    "working_tax_credit_reported",
]
TAX_CREDITS = ["child_tax_credit_reported", "working_tax_credit_reported"]


class is_qualifying_young_person_for_uc_education(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person for the Universal Credit education condition"
    documentation = (
        "Whether this person counts as a qualifying young person for the "
        "Universal Credit condition that a claimant is not receiving "
        "education: they meet is_qualifying_young_person_for_universal_credit "
        "and have no entitlement to an existing benefit. Under the Universal "
        "Credit (Transitional Provisions) Regulations 2014 reg. 28, a person "
        "entitled to an existing benefit doesn't count as a qualifying young "
        "person, and the Secretary of State lists the existing benefits in "
        "reg. 2(1): income-based Jobseeker's Allowance, income-related "
        "Employment and Support Allowance, Income Support, Housing Benefit, "
        "Child Tax Credit and Working Tax Credit. The model reads entitlement "
        "from the year's reported receipt: the person's own report of any of "
        "them, or, for a claimant or partner, either member's report of tax "
        "credits, which a couple claims jointly. A person outside the "
        "definition under reg. 28 takes the ordinary route under the Universal "
        "Credit Regulations 2013 reg. 12(2). The model's other rules read "
        "is_qualifying_young_person_for_universal_credit, which leaves reg. 28 "
        "out. In Northern Ireland the decision maker applies the same rule "
        "under reg. 29 of the Universal Credit (Transitional Provisions) "
        "Regulations (Northern Ireland) 2016, with reg. 6 of the Universal "
        "Credit Regulations (Northern Ireland) 2016 in place of the Universal "
        "Credit Regulations 2013 reg. 5."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/29",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/6",
    )

    def formula(person, period, parameters):
        qualifying_young_person = person(
            "is_qualifying_young_person_for_universal_credit", period
        )
        # SI 2014/1230 reg. 28: where a person who would be a qualifying
        # young person "is entitled to an existing benefit", "that person is
        # not a qualifying young person for the purposes of the Universal
        # Credit Regulations".
        own_award = add(person, period, EXISTING_BENEFITS) > 0
        # Tax Credits Act 2002 s. 3(3)(a): the members of a couple claim a
        # tax credit jointly, so the award belongs to both.
        claimant_or_partner = person("is_claimant_or_partner", period)
        joint_tax_credits = claimant_or_partner & (
            person.benunit.sum(claimant_or_partner * add(person, period, TAX_CREDITS))
            > 0
        )
        return qualifying_young_person & ~(own_award | joint_tax_credits)
