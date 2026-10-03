from policyengine_uk.model_api import *


class receives_severe_disability_premium_qualifying_benefit(Variable):
    value_type = bool
    entity = Person
    label = "Receives a severe disability premium qualifying benefit"
    documentation = (
        "In receipt of a benefit that makes a claimant or partner severely "
        "disabled for the legacy severe disability premium: attendance "
        "allowance (either rate), the care component of disability living "
        "allowance at the highest or middle rate, the daily living component "
        "of personal independence payment at either rate, or armed forces "
        "independence payment. The same receipt makes a non-dependant "
        "ignored in the premium's residence condition. Armed Forces "
        "Compensation Scheme payments other than armed forces independence "
        "payment do not qualify. The Scottish equivalents (adult disability "
        "payment, pension age disability payment, Scottish adult disability "
        "living allowance and, in Housing Benefit and the Scottish Council "
        "Tax Reduction scheme, the care component of child disability "
        "payment) are not separate model variables; the "
        "lists differ slightly between instruments (pension age disability "
        "payment is not in the IS and JSA single-claimant lists). The "
        "hospital and concessionary-payment rules are not modelled. "
        "Household country selects the qualifying-benefit list: Northern "
        "Ireland adds armed forces independence payment from 24 December "
        "2013 and PIP daily living from 20 June 2016; Great Britain adds "
        "both from 8 April 2013. The model reads each list as at 30 April "
        "of the year from 2015 and at 1 January before that, without "
        "within-year proration. The initial parameter "
        "value date preserves the shared model baseline; Northern Ireland "
        "historical coverage before 20 November 2006 has not been verified."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2008/794/schedule/4/paragraph/6",
        "https://www.legislation.gov.uk/uksi/1996/207/schedule/1/paragraph/15",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4/paragraph/14",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/1/made",
        "https://www.legislation.gov.uk/uksi/2013/3021/article/1",
        "https://www.legislation.gov.uk/nisr/2016/228/regulation/1",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.disability_premia
        country = person.household("country", period)
        northern_ireland = country == country.possible_values.NORTHERN_IRELAND
        return where(
            northern_ireland,
            add(person, period, p.severe_qualifying_benefits_northern_ireland) > 0,
            add(person, period, p.severe_qualifying_benefits) > 0,
        )
