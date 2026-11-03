from policyengine_uk.model_api import *


class tax_free_childcare_qualifying_temporary_absence(Variable):
    """Reported regulation 12 status for the modeled childcare accounts."""

    value_type = bool
    entity = Person
    label = "Qualifying temporary absence for Tax-Free Childcare"
    documentation = (
        "Whether regulation 12 of the Childcare Payments (Eligibility) "
        "Regulations 2015 applies to this person for the childcare accounts "
        "and declaration periods being modeled. True asserts a listed "
        "absence or statutory-pay condition under regulation 12(1), and "
        "qualifying paid work immediately before it, or a preceding period "
        "covered by another regulation 12 route, under regulation 12(3). "
        "For an account belonging to a child whose birth or adoption caused "
        "the absence, it also asserts the applicable-period condition in "
        "regulations 12(4) and 9(2A). The caller must establish these "
        "conditions for each modeled account and declaration period. The "
        "annual model does not infer prior work, return-to-work dates, "
        "birth or adoption dates, or account-specific windows. Annual or "
        "sick leave under regulation 14 alone, or a statutory-pay amount "
        "alone, does not establish this status. Other eligibility conditions, "
        "including the adjusted net income limit, still apply."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/12",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/9",
    )
