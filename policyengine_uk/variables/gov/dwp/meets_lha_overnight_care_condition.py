from policyengine_uk.model_api import *


class meets_lha_overnight_care_condition(Variable):
    value_type = bool
    entity = Person
    label = "Meets the LHA overnight care condition"
    documentation = (
        "Whether this person receives a qualifying disability benefit "
        "(attendance allowance or armed forces independence payment, the "
        "care component of Disability Living Allowance at the middle or "
        "highest rate, or the daily living component of Personal "
        "Independence Payment) and has non-resident carers who regularly "
        "stay overnight to care for them. This is the Universal Credit "
        "overnight care condition and the Housing Benefit 'person who "
        "requires overnight care'. Two Housing Benefit routes are not "
        "modelled: a person without a qualifying benefit whose need the "
        "local authority accepts on other evidence, and the requirement that "
        "the carers have the use of a bedroom additional to the occupiers'."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/2",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.LHA
        # UC Regs 2013 Sch 4 para 12(3)(a); HB Regs 2006 reg 2(1), "person
        # who requires overnight care", (a)(i)-(iib).
        qualifying_benefit = add(person, period, p.overnight_care_benefits) > 0
        # UC para 12(3)(b)-(c); HB reg 2(1), (b).
        return qualifying_benefit & person("has_non_resident_overnight_carer", period)
