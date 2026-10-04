from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import MONTHS_FROM_TAX_YEAR_START_TO_MID_YEAR


class ni_class_4_liable(Variable):
    value_type = bool
    entity = Person
    label = "liable for Class 4 National Insurance by age"
    documentation = (
        "Whether the person is liable for Class 4 contributions for the tax "
        "year by their age. A person over State Pension age at the beginning of "
        "the tax year (6 April) is excepted; a person who reaches it during the "
        "year stays liable for the whole year. People under 16 are treated as "
        "excepted, as they can be on application under regulation 93. The model "
        "also excepts someone reaching State Pension age on 6 April itself. "
        "With default whole-number household ages, the inferred birthday is "
        "6 April, so entering an integer State Pension age makes this boundary "
        "reading determine the Class 4 result. Explicit birthday-month inputs "
        "and fractional ages can place the birthday on another day."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2001/1004/regulation/91",
        "https://www.legislation.gov.uk/uksi/2001/1004/regulation/93",
        "https://www.gov.uk/hmrc-internal-manuals/national-insurance-manual/nim24510",
    )

    def formula(person, period, parameters):
        # Social Security (Contributions) Regulations 2001 reg 91(a): an
        # earner who "at the beginning of a year of assessment is over
        # pensionable age" is excepted from Class 4 liability. Neither the
        # regulations nor HMRC's manual (NIM24510) address someone who
        # attains pensionable age on 6 April itself.
        # This reads them as over it at the beginning of that year:
        # pensionable age is attained at the commencement of the day, and
        # the enabling power (SSCBA 1992 s.17(2)(b)) is for "a person having
        # attained pensionable age".
        # Default whole-number household ages put the birthday on 6 April
        # (six months before 6 October). At an integer State Pension age,
        # this boundary reading therefore determines that household's result.
        over_pension_age_at_start_of_year = (
            person("months_since_state_pension_age", period)
            >= MONTHS_FROM_TAX_YEAR_START_TO_MID_YEAR
        )
        return person("over_16", period) & ~over_pension_age_at_start_of_year
