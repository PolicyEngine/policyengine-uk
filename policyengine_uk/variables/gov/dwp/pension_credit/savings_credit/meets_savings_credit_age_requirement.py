from policyengine_uk.model_api import *


class meets_savings_credit_age_requirement(Variable):
    value_type = bool
    entity = Person
    label = "Meets the Savings Credit age condition"
    documentation = (
        "The first Savings Credit condition in SPCA 2002 s.3(1)(a), for this "
        "person. Until 5 April 2016 it was attaining the age of 65. From "
        "6 April 2016 the person must have attained pensionable age before "
        "that date and have attained 65. Pensionable age depends on the date "
        "of birth (Pensions Act 1995 Sch. 4 para. 1), so the test is being "
        "born before 6 April 1951 (men) or 6 April 1953 (women). The model has "
        "no date of birth: a person aged A in the year starting 6 April Y is "
        "taken to turn A during that year, so to be born between 6 April "
        "Y - A and 5 April Y - A + 1. Each such window lies wholly before or "
        "wholly after 6 April of the limit year, so the test compares birth "
        "years, as the Universal Credit and Child Tax Credit tests for being "
        "born before 6 April 2017 do."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/3",
        "https://www.legislation.gov.uk/ukpga/1995/26/schedule/4/paragraph/1",
    )

    def formula(person, period, parameters):
        # s.3(1)(a) as enacted: "has attained the age of 65". The Pensions Act
        # 2007 Sch. 1 para. 44 substitution of "pensionable age" never took
        # effect: it was due from 6 April 2024 (s.13(3)), then 6 December 2018
        # (Pensions Act 2011 Sch. 1 para. 9(b)), and was omitted from 6 April
        # 2016 by the Pensions Act 2014 Sch. 12 para. 91.
        p = parameters(period).gov.dwp.pension_credit.savings_credit.age_requirement
        return person("age", period) >= p.minimum_age

    def formula_2016(person, period, parameters):
        # s.3(1)(a) as substituted from 6 April 2016 by the Pensions Act 2014
        # Sch. 12 para. 89: "has attained pensionable age before 6 April 2016
        # and has attained the age of 65".
        p = parameters(period).gov.dwp.pension_credit.savings_credit.age_requirement
        birth_year_limit = where(
            person("is_male", period),
            p.birth_year_limit.male,
            p.birth_year_limit.female,
        )
        attained_pensionable_age_before_6_april_2016 = (
            person("birth_year", period) < birth_year_limit
        )
        return attained_pensionable_age_before_6_april_2016 & (
            person("age", period) >= p.minimum_age
        )
