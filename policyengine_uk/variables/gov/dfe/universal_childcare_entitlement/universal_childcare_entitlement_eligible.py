from policyengine_uk.model_api import *


class universal_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible for universal childcare entitlement"
    definition_period = YEAR
    defined_for = "would_claim_universal_childcare"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2006/21/section/7",
        "https://www.legislation.gov.uk/ukpga/2016/5/section/1",
    )

    def formula(person, period, parameters):
        country = person.household("country", period)
        countries = country.possible_values
        in_england = country == countries.ENGLAND
        # Childcare (Early Years Provision Free of Charge) Regulations 2016 (part 33)
        # The regulation above requires an "English local authority" to secure early years provision, limiting the entitlement to England.

        age = person("age", period)
        p = parameters(period).gov.dfe.universal_childcare_entitlement
        meets_age_condition = (age >= p.age.min) & (age < p.age.max)
        not_compulsory_age = ~person("is_of_compulsory_school_age", period)

        # Eligibility for the working parent entitlement does not remove the
        # universal hours: Childcare Act 2016 s.1(6)(a) counts them towards
        # the working parent's 30 hours, which extended_childcare_entitlement
        # then tops up.

        # Section 7 of the Childcare Act 2006
        # The regulation above limits free early years provision to children under compulsory school age.
        return in_england & meets_age_condition & not_compulsory_age
