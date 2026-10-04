from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_supported_scheme,
)


class council_tax_reduction_claim_scheme_supported(Variable):
    value_type = bool
    entity = BenUnit
    label = "The model simulates this family's Council Tax Reduction"
    documentation = (
        "Whether the family's Council Tax Reduction is simulated rather than "
        "taken as reported (council_tax_benefit). Where the household has a "
        "single claim, this is council_tax_reduction_scheme_supported. Where "
        "families share the rent and each claims on its part, a claiming "
        "family is simulated if the model simulates the scheme its own claim "
        "falls under, so a working-age sharer in a council whose working-age "
        "scheme is not modelled keeps a reported reduction beside a pensioner "
        "whose reduction is simulated. A family that cannot claim there is "
        "simulated, at nil, where any claim in the household is, since the "
        "simulated claims cover those families' shares of the bill."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2012/2885/regulation/3"

    def formula(benunit, period, parameters):
        household = benunit.household
        own_scheme = is_supported_scheme(
            household("country", period),
            benunit("council_tax_reduction_claim_pensioner", period),
            household("local_authority", period),
        )
        claimant = benunit("council_tax_reduction_claimant_benunit", period)
        person = benunit.members
        any_claim_simulated = benunit.any(
            person.household.any(benunit.project(claimant & own_scheme))
        )
        return where(
            household("council_tax_reduction_claims_are_joint", period),
            where(claimant, own_scheme, any_claim_simulated),
            household("council_tax_reduction_scheme_supported", period),
        )
