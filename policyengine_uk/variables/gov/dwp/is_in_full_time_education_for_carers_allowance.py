from policyengine_uk.model_api import *


class is_in_full_time_education_for_carers_allowance(Variable):
    value_type = bool
    entity = Person
    label = "Receiving full-time education for Carer's Allowance"
    documentation = (
        "Whether this person receives full-time education for Carer's "
        "Allowance under section 70(3) of the applicable Great Britain or "
        "Northern Ireland Act. The user or dataset supplies this "
        "programme-specific legal classification; the model does not derive "
        "it from current_education, in_HE or is_in_full_time_education. "
        "Core may carry an earlier year's supplied status; the user or "
        "dataset must update the annual input when that status changes. "
        "The default False is a non-exclusion assumption only when no input "
        "can carry, not evidence that the person is outside education. This "
        "annual input represents a constant status and cannot date or "
        "prorate course starts, ends or other changes within the year. "
        "In Great Britain only, regulation 5 treats attendance on a course "
        "at an educational establishment for 21 hours or more a week as "
        "full-time education. Count instruction, tuition, supervised study, "
        "examinations, practical work and curriculum exercises, experiments "
        "or projects; exclude meal breaks and unsupervised study. Keep the "
        "usual weekly hours during vacations or temporary interruptions "
        "until the course ends or the person abandons it or is dismissed. "
        "For Northern Ireland, supply the status under its applicable "
        "Carer's Allowance rules; this input does not apply Great Britain's "
        "counted-hours definition there."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/ukpga/1992/7/section/70",
        "https://www.legislation.gov.uk/uksi/1976/409/regulation/5",
        "https://www.nidirect.gov.uk/articles/carers-allowance",
    )
