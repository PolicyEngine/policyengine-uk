from policyengine_uk.model_api import *


class uc_housing_costs_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit housing costs element"
    documentation = (
        "The Universal Credit housing costs element for a renter: eligible "
        "rent, limited for a private renter by the Local Housing Allowance "
        "(uc_LHA_cap), less non-dependant deductions. The Secretary of State "
        "excludes payments for specified or temporary accommodation from "
        "rent payments (UC Regs 2013 Sch 1 paras 3(h), 3(i), 3A and 3B; NI: "
        "SR 2016/216 Sch 1 paras 3(e), 3(ea), 4 and 4A), so the element is "
        "nil for a family with in_specified_or_temporary_accommodation; "
        "Housing Benefit pays that rent instead (housing_benefit_eligible)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/1/paragraph/3A",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/1/paragraph/3B",
        "https://www.legislation.gov.uk/nisr/2016/216/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/nisr/2016/216/schedule/1/paragraph/4",
        "https://www.legislation.gov.uk/nisr/2016/216/schedule/1/paragraph/4A",
    )

    def formula(benunit, period, parameters):
        # The family's own tenure: a boarder or lodger is a private renter
        # whatever the household's tenure (UC Regs 2013 Sch 4 para 20).
        tenure_type = benunit("benunit_tenure_type", period)
        tenure_types = tenure_type.possible_values
        rent = benunit("benunit_rent", period)
        # Universal Credit has its own monthly national maximum, which is
        # set independently of the weekly Housing Benefit one.
        rent_cap = benunit("uc_LHA_cap", period)
        capped_rent_amount = min_(rent_cap, rent)
        max_housing_costs = select(
            [
                (tenure_type == tenure_types.RENT_FROM_COUNCIL)
                | (tenure_type == tenure_types.RENT_FROM_HA),
                tenure_type == tenure_types.RENT_PRIVATELY,
            ],
            [rent, capped_rent_amount],
            default=0,
        )
        non_dependent_deductions = benunit("uc_non_dep_deductions", period)
        # Payments for specified or temporary accommodation aren't rent
        # payments (Sch 1 para 3(h) and (i); NI: SR 2016/216 Sch 1 para 3(e)
        # and (ea)), so they bring no housing costs element.
        excluded = benunit("in_specified_or_temporary_accommodation", period)
        element = max_(max_housing_costs - non_dependent_deductions, 0)
        return where(excluded, 0, element)
