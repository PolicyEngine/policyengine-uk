from policyengine_uk.model_api import *


class early_years_school_start_deferred(Variable):
    value_type = bool
    entity = Person
    label = "school start deferred, keeping funded early years hours"
    documentation = (
        "Whether a child keeps funded early years hours for the whole year "
        "although its date of birth puts its start at school in this year's "
        "autumn term (early_years_term_share_before_school). That is so when "
        "its start is deferred: in England until later in the school year, "
        "or a year for a summer-born child admitted out of its age group; in "
        "Scotland for a deferred primary 1 year, funded since August 2023 "
        "(SSI 2021/67). Set it too for a child who takes its funded hours in "
        "a council-funded independent school reception class, where they are "
        "still delivered as early years hours."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.gov.uk/government/publications/school-admissions-code--2",
        "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026",
        "https://www.legislation.gov.uk/ssi/2021/67/made",
    )
