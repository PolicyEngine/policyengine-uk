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


class is_qualifying_young_person_on_uc_migration_day(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person on the Universal Credit migration day"
    documentation = (
        "Whether this person counted as a qualifying young person for the "
        "Universal Credit condition that a claimant is not receiving "
        "education on the migration day of a closure claim, the day before "
        "the Universal Credit award starts (Universal Credit (Transitional "
        "Provisions) Regulations 2014 reg. 49). Under reg. 28, a person "
        "entitled to an existing benefit doesn't count as a qualifying young "
        "person, and the Secretary of State lists the existing benefits in "
        "reg. 2(1). Under reg. 8(2)(a), a claim for Universal Credit ends a "
        'tax credit award "on the day before the first date on which the '
        'claimant is entitled to universal credit", so on the migration day '
        "reg. 28 still applied to that award. The model reads the year's "
        "reported receipt of an existing benefit as that award, whether or "
        "not it still pays the benefit that year: the person's own report, "
        "or, for a claimant or partner, either member's report of tax "
        "credits, which a couple claims jointly. "
        "uc_is_excepted_from_education_condition reads this status for the "
        "reg. 60(1) protection. In Northern Ireland the decision maker applies "
        "the same rules under regs. 6(2), 29 and 50 of the Universal Credit "
        "(Transitional Provisions) Regulations (Northern Ireland) 2016."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/2",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/49",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/6",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/29",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/50",
    )

    def formula(person, period, parameters):
        qualifying_young_person = person(
            "is_qualifying_young_person_for_universal_credit", period
        )
        # SI 2014/1230 reg. 28: where a person who would be a qualifying
        # young person "is entitled to an existing benefit", "that person is
        # not a qualifying young person for the purposes of the Universal
        # Credit Regulations". The report stands for the award the closure
        # claim ended, so the formula reads it in every year.
        own_award = add(person, period, EXISTING_BENEFITS) > 0
        # Tax Credits Act 2002 s. 3(3)(a): the members of a couple claim a
        # tax credit jointly, so the award belongs to both.
        claimant_or_partner = person("is_claimant_or_partner", period)
        joint_tax_credits = claimant_or_partner & (
            person.benunit.sum(claimant_or_partner * add(person, period, TAX_CREDITS))
            > 0
        )
        return qualifying_young_person & ~(own_award | joint_tax_credits)
