from policyengine_uk.model_api import *


class council_tax_reduction_household_has_simulated_claim(Variable):
    value_type = bool
    entity = Household
    label = "A Council Tax Reduction claim in the household is simulated"
    documentation = (
        "Whether any family that claims Council Tax Reduction for the "
        "household falls under a scheme the model simulates. The simulated "
        "awards then cover those families' shares of the council tax. A "
        "reported reduction of a family the model does not treat as liable "
        "cannot be reconciled with them, so it is not kept."
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        person = household.members
        claimant = person.benunit("council_tax_reduction_claimant_benunit", period)
        supported = person.benunit("council_tax_reduction_scheme_supported", period)
        return household.any(claimant & supported)
