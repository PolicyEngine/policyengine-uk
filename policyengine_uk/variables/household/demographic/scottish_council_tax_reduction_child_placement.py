from policyengine_uk.model_api import *


class ScottishCouncilTaxReductionChildPlacement(Enum):
    FOSTER_CARER = "Placed with a foster carer"
    APPROVED_KINSHIP_CARER = "Placed with or living with an approved kinship carer"
    PARENT_OR_PARENTAL_RESPONSIBILITY = (
        "Placed with or living with a parent or person with parental responsibility"
    )
    OTHER_LOOKED_AFTER = "Other looked-after arrangement"
    UNSPECIFIED = "Use existing looked-after status"


class scottish_council_tax_reduction_child_placement(Variable):
    value_type = Enum
    possible_values = ScottishCouncilTaxReductionChildPlacement
    default_value = ScottishCouncilTaxReductionChildPlacement.UNSPECIFIED
    entity = Person
    label = "Scottish Council Tax Reduction child placement"
    definition_period = YEAR
    documentation = (
        "The placement of a child looked after by a local authority for "
        "Scotland's working-age Council Tax Reduction child test from April "
        "2022. This input refines only a person flagged is_looked_after_child; "
        "it does not change that flag, Universal Credit or any other scheme. "
        "For foster, approved kinship and other looked-after arrangements, "
        "also set is_looked_after_by_local_authority to true. For a placement "
        "with a parent or a person with parental responsibility, keep that "
        "existing input false under its Universal Credit exception convention. "
        "UNSPECIFIED retains the existing exclusion for a flagged child. "
        "This compatibility fallback does not identify an unknown placement "
        "as a foster placement or impute any placement. Before 31 October "
        "2024 the Scottish rule excepts parent, parental responsibility and "
        "approved kinship arrangements; from that date it excludes only "
        "foster placements. The model's annual parameter conversion samples "
        "30 April, so annual 2024 retains the earlier rule and annual 2025 "
        "uses the amended rule."
    )
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/7/2022-04-01",
        "https://www.legislation.gov.uk/ssi/2024/230/made",
    )
