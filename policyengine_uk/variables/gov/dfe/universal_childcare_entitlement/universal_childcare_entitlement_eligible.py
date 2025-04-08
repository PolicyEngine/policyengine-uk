from policyengine_uk.model_api import *


class universal_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible for universal childcare entitlement"
    definition_period = YEAR
    defined_for = "would_claim_universal_childcare"

    def formula(person, period, parameters):
        country = person.household("country", period)
        countries = country.possible_values
        in_england = country == countries.ENGLAND
        # Childcare (Early Years Provision Free of Charge) Regulations 2016 (part 33)
        # The regulation above requires an "English local authority" to secure early years provision, limiting the entitlement to England.

        age = person("age", period)
        p = parameters(period).gov.dfe.universal_childcare_entitlement
        meets_age_condition = (age >= p.min_age) & (age < p.max_age)
        not_compulsory_age = ~person("is_of_compulsory_school_age", period)

        # Check if person has extended childcare. If so, they are not eligible. Combining extended childcare and universal childcare is not allowed.
        # https://www.childcarechoices.gov.uk/combining-schemes
        has_extended_childcare = person.benunit(
            "extended_childcare_entitlement_eligible", period
        )

        # Section 7 of the Childcare Act 2006
        # The regulation above limits free early years provision to children under compulsory school age.
        return (
            in_england
            & meets_age_condition
            & not_compulsory_age
            & ~has_extended_childcare
        )
