from policyengine_uk.model_api import *


class esa_income_payable_share(Variable):
    value_type = float
    entity = Person
    label = "Share of the year an income-related ESA award stays payable"
    documentation = (
        "Share of the year for which the old style income-related ESA award "
        "on this person's report stays payable. SI 2025/1148 art. 3A brought "
        "the abolition of income-related ESA (Welfare Reform Act 2012 "
        "s.33(1)(b)) into force for every remaining award on 1 July 2026, and "
        "SR 2025/176 art. 3A brought it into operation in Northern Ireland on "
        "1 October 2026. So this is the share of the fiscal year before the "
        "household's date (gov.dwp.ESA.income.awards_payable): 1 up to "
        "2025-26; in 2026-27, 86 of 365 days in Great Britain and 178 of 365 "
        "in Northern Ireland; and 0 from 2027-28. An award saved for an "
        "appointee (esa_income_appointee_saving) has a share of 1 in every "
        "year. esa_income pays each award for this share of the year, and "
        "esa_income_report_closed ends the report in a year where it is 0. A "
        "contributory allowance continues as new style ESA (esa_contrib)."
    )
    definition_period = YEAR
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/uksi/2025/1148/article/3A",
        "https://www.legislation.gov.uk/nisr/2025/176/article/3A",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/33",
        "https://www.legislation.gov.uk/nisi/2015/2006/article/39",
    )

    def formula(person, period, parameters):
        payable = parameters(period).gov.dwp.ESA.income.awards_payable
        country = person.household("country", period)
        # Great Britain's date applies everywhere but Northern Ireland,
        # including an unknown country.
        share = where(
            country == country.possible_values.NORTHERN_IRELAND,
            payable.northern_ireland,
            payable.great_britain,
        )
        # Art. 3A(2) saves an award for an appointee in every year.
        return where(person("esa_income_appointee_saving", period), 1, share)
