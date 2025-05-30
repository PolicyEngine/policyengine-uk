from policyengine_uk.model_api import *


class private_school_vat(Variable):
    label = "private school VAT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        num_children = add(household, period, ["attends_private_school"])

        ps_vat_params = parameters(period).gov.simulation.private_school_vat
        private_school_vat_basis = ps_vat_params.private_school_vat_basis
        avg_yearly_private_school_cost = ps_vat_params.private_school_fees

        private_school_vat_rate = parameters(
            period
        ).gov.contrib.labour.private_school_vat

        return (
            num_children
            * avg_yearly_private_school_cost
            * private_school_vat_rate
            * private_school_vat_basis
        )
