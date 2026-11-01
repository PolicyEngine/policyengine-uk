from policyengine_uk.model_api import *


class receives_enhanced_disability_premium_qualifying_benefit(Variable):
    value_type = bool
    entity = Person
    label = "Receives an enhanced disability premium qualifying benefit"
    documentation = (
        "In receipt of a benefit that meets the qualifying-benefit condition "
        "of the legacy enhanced disability premium: the care component of "
        "disability living allowance at the highest rate, the daily living "
        "component of personal independence payment at the enhanced rate, or "
        "armed forces independence payment. The award categories "
        "(dla_sc_category, pip_dl_category) decide the rate, as in the severe "
        "disability premium list (receives_severe_disability_premium_"
        "qualifying_benefit), so a DLA or PIP amount entered without its "
        "category does not count. Each programme adds its own conditions: "
        "the age limit (num_enhanced_disabled_claimants_or_partners_for_"
        "legacy_benefits) and, in Council Tax Reduction, its scheme's own list "
        "(meets_council_tax_reduction_enhanced_disability_premium_condition). "
        "Attendance allowance does not qualify. The Scottish equivalents "
        "(child disability payment and Scottish adult disability living "
        "allowance care components at the highest rate, adult disability "
        "payment daily living component at the enhanced rate) are not "
        "separate model variables. The limited capability for work-related "
        "activity limb (Housing Benefit), the support component limb "
        "(Employment and Support Allowance), the hospital rules and the "
        "long-term patient exclusion are not modelled. Household country "
        "selects the list: Northern Ireland adds armed forces independence "
        "payment from 24 December 2013 and PIP daily living from 20 June "
        "2016; Great Britain adds both from 8 April 2013. The model reads each "
        "list as at 30 April of the year from 2015, without within-year "
        "proration."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/15",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13A",
        "https://www.legislation.gov.uk/uksi/2008/794/schedule/4/paragraph/7",
        "https://www.legislation.gov.uk/uksi/1996/207/schedule/1/paragraph/15A",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4/paragraph/15",
        "https://www.legislation.gov.uk/nisr/2008/280/schedule/4/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/12",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.disability_premia
        country = person.household("country", period)
        northern_ireland = country == country.possible_values.NORTHERN_IRELAND
        return where(
            northern_ireland,
            add(person, period, p.enhanced_qualifying_benefits_northern_ireland) > 0,
            add(person, period, p.enhanced_qualifying_benefits) > 0,
        )
