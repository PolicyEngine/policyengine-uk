from policyengine_uk.model_api import *


class is_uc_claimant(Variable):
    """Claimant or partner, rather than a child or qualifying young person.

    A Universal Credit claim is made by a single claimant or by the members of
    a couple jointly; children and qualifying young persons are people a
    claimant is responsible for. This is the benefit unit's claimant or
    partner (`is_claimant_or_partner`). It does not establish eligibility:
    the UC age and other basic conditions are applied separately.
    """

    value_type = bool
    entity = Person
    label = "Universal Credit claimant or partner"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/39",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/40",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3/2",
    )

    def formula(person, period, parameters):
        return person("is_claimant_or_partner", period)
