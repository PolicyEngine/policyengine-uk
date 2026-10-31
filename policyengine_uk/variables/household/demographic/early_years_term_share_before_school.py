from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day, term_starts

# The month and day each nation's school cohort is born from: a child born on
# or after it starts school a year later than one born earlier in the same
# calendar year.
# - England and Wales: the September following the fourth birthday (School
#   Admissions Code 2021 para 2.17), so the cohort runs from 1 September.
# - Scotland: primary 1 starts in August for children who turn five by the
#   council's latest date (Education (Scotland) Act 1980 s.32), the end of
#   February, so the cohort runs from 1 March.
# - Northern Ireland: primary 1 starts in September for children who are four
#   by 1 July (Education and Libraries (Northern Ireland) Order 1986 art
#   46(2)), so the cohort runs from 2 July.
COHORT_STARTS = {
    "ENGLAND": 901,
    "WALES": 901,
    "SCOTLAND": 301,
    "NORTHERN_IRELAND": 702,
}


class early_years_term_share_before_school(Variable):
    value_type = float
    entity = Person
    label = "share of the year's terms before a child starts school"
    documentation = (
        "The share of the year's three terms, beginning on 1 April and 1 "
        "September of the year and 1 January of the next, that begin before "
        "the child starts school. Funded early years hours stop then: a "
        "reception place meets England's universal and working parent "
        "duties, and a child at primary school is not an eligible pre-school "
        "child in Scotland. The start comes from the date of birth. In "
        "England and Wales a child starts reception in the September "
        "following its fourth birthday. In Scotland primary 1 starts in "
        "August for children who turn five from March to the next February. "
        "In Northern Ireland it starts in September for children who are "
        "four by 1 July. So most 4-year-olds start school during the year "
        "and keep only the summer term: in England, those aged 4 on 6 "
        "October whose fourth birthday was before 1 September. A child whose "
        "start is deferred keeps the whole year "
        "(early_years_school_start_deferred). A situation that sets this "
        "share directly for some people gives the others 1."
    )
    definition_period = YEAR
    unit = "/1"
    default_value = 1
    reference = (
        "https://www.gov.uk/government/publications/school-admissions-code--2",
        "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026",
        "https://www.legislation.gov.uk/asp/2014/8/section/47",
        "https://www.legislation.gov.uk/ukpga/1980/44/section/32",
        "https://www.legislation.gov.uk/nisi/1986/594/article/46",
    )

    def formula(person, period, parameters):
        born = birth_day(person, period)
        country = person.household("country", period)
        countries = country.possible_values
        cohort_start = np.select(
            [country == getattr(countries, name) for name in COHORT_STARTS],
            list(COHORT_STARTS.values()),
            default=COHORT_STARTS["ENGLAND"],
        )
        start_year = born // 10_000 + 4 + (born % 10_000 >= cohort_start)
        # Scotland's August start comes between the summer and autumn terms,
        # so every nation's school year starts with its autumn term.
        school_start = start_year * 10_000 + 901
        starts = term_starts(period.start.year)
        share = sum(start < school_start for start in starts) / len(starts)
        deferred = person("early_years_school_start_deferred", period)
        return where(deferred, 1, share)
