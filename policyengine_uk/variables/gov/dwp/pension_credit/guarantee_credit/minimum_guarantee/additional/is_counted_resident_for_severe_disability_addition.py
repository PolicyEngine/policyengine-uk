from policyengine_uk.model_api import *


class is_counted_resident_for_severe_disability_addition(Variable):
    value_type = bool
    entity = Person
    label = (
        "Counts as another resident for the Pension Credit severe disability addition"
    )
    documentation = (
        "Aged 18 or over and not a person whose presence is ignored under "
        "State Pension Credit Regulations 2002 Sch I para 2. Modelled "
        "exceptions: a recipient of a qualifying disability benefit (para "
        "2(2)(a)), a person certified blind or severely sight impaired (para "
        "2(2)(b)), and a qualifying young person within regulation 4A (para "
        "2(2)(f); a child under 16 is below the age limit anyway). Not "
        "modelled, because the data do not identify them: sight regained "
        "within 28 weeks (2(2)(c)), a carer engaged by a charity and their "
        "partner (2(2)(d)-(e)), a carer in their first 12 weeks in the "
        "household (2(3)-(4)), commercial lodgers and landlords who are not "
        "close relatives (2(5)), joint occupiers and their partners (2(6)-(7)), "
        "and people who share only a bathroom, lavatory or communal area or "
        "are separately liable to the landlord (para 3). Each unmodelled "
        "exception ignores a person, so leaving it out can only withhold the "
        "addition. Whether the person resides with a given claimant is decided "
        "by meets_severe_disability_addition_residence_condition."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/3",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.guarantee_credit
        adult = person("age", period) >= p.severe_disability.other_resident_age_limit
        ignored = (
            person("receives_severe_disability_addition_qualifying_benefit", period)
            | person("is_blind", period)
            | person("is_qualifying_young_person_for_pension_credit", period)
        )
        return adult & ~ignored
