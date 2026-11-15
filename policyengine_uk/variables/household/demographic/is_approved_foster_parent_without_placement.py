from policyengine_uk.model_api import *


class is_approved_foster_parent_without_placement(Variable):
    value_type = bool
    entity = Person
    label = "approved foster parent between placements"
    documentation = (
        "Whether this person is an approved foster parent (in Scotland, a "
        "foster carer or kinship carer) with no child currently placed with "
        "them, whose last placement ended, or who was approved and has had "
        "no placement since, no more than 12 months ago. Housing Benefit's "
        "limit is 52 weeks. Such a person keeps the foster parent's "
        "additional bedroom (UC Regs 2013 Sch 4 para 12(5); HB Regs 2006 "
        "reg 2(1), 'qualifying parent or carer')."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
    )
