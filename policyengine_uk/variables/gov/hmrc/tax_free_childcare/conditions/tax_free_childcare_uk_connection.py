from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.immigration_status import (
    ImmigrationStatus,
)


class tax_free_childcare_uk_connection(Variable):
    value_type = bool
    entity = Person
    label = "UK connection for tax-free childcare"
    documentation = (
        "Whether the person meets the UK connection requirement for "
        "tax-free childcare as specified in The Childcare Payments "
        "(Eligibility) Regulations 2015, regulations 7 and 8"
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        # Regulation 7: Must be ordinarily resident in the UK
        is_in_uk = person("is_in_uk", period)

        # Regulation 7(3): Not treated as in UK if subject to immigration
        # control, unless exempt under Regulation 8
        immigration_status = person("immigration_status", period)
        statuses = immigration_status.possible_values

        # Immigration statuses that are subject to immigration control
        # and NOT exempt under Regulation 8
        subject_to_control_not_exempt = immigration_status == statuses.VISA_HOLDER

        # Regulation 8 exempt statuses (not subject to immigration control
        # exclusion): refugee, humanitarian protection, discretionary leave
        # UK citizens and settled status holders are not subject to
        # immigration control at all

        # Person meets UK connection if:
        # 1. Ordinarily resident in UK, AND
        # 2. Not subject to immigration control (or exempt under Reg 8)
        return is_in_uk & ~subject_to_control_not_exempt
