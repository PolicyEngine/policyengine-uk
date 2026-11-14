from policyengine_uk.model_api import *


class housing_benefit_report_is_rate_rebate_only(Variable):
    value_type = bool
    entity = Person
    label = "Housing Benefit report covers only a Northern Ireland rate rebate"
    documentation = (
        "Whether this person's housing_benefit_reported covers only a rate "
        "rebate on the home they occupy in Northern Ireland, with no rent "
        "rebate or allowance. The Housing Benefit Regulations (Northern "
        "Ireland) 2006 (SR 2006/405) and their twin for people at the "
        "qualifying age for State Pension Credit (SR 2006/406) pay a rate "
        "rebate on rates (reg. 12(1)) and a rent rebate or allowance on rent "
        "and similar payments (reg. 13(1)), including mooring charges for a "
        "houseboat and site payments for a caravan or mobile home (reg. "
        "13(1)(f) and (g)). So tenure doesn't settle the form: an owner can "
        "get a rent allowance. A Universal Credit claim ends a rate rebate the "
        "day before the award starts (SR 2016/226 reg. 6(2)) and runs a rent "
        "rebate or allowance on for two weeks (reg. 6(2A)). Only the first-day "
        "test that is_qualifying_young_person_for_uc_education reads uses this "
        "status, and only in Northern Ireland. A person with both forms leaves "
        "it false, because their rent rebate or allowance runs on. It has no "
        "formula and defaults to False, so the model reads a report as a rent "
        "rebate or allowance unless this input says otherwise."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/12",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/13",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/12",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/13",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/6",
    )
