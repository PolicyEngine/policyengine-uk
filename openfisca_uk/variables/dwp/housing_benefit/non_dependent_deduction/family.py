from openfisca_uk.model_api import *


class hb_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Non-dependent deductions"
    documentation = "The non-dependent deductions to made from this family's Housing Benefit claim."
    definition_period = YEAR
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/74/made"

    def formula(benunit, period, parameters):
        non_dep_deductions_in_hh = benunit.max(
            add(benunit.members.household, period, ["hb_individual_non_dep_deduction"])
        )
        non_dep_deductions_in_bu = add(
            benunit, period, ["hb_individual_non_dep_deduction"]
        )
        return non_dep_deductions_in_hh - non_dep_deductions_in_bu

