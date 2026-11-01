from policyengine_uk.model_api import *


class esa_income_payable_share(Variable):
    value_type = float
    entity = Person
    label = "Share of the year the income-related ESA claim stays payable"
    documentation = (
        "Share of the year for which the old style income-related ESA claim "
        "this person belongs to stays payable. The claimant and partner share "
        "one claim; any other member claims in their own right. The Secretary "
        "of State appointed 1 July 2026 for the abolition of income-related "
        "ESA (Welfare Reform Act 2012 s.33(1)(b)) to reach every remaining "
        "award (SI 2025/1148 art. 3A(1)), and the Department appointed 1 "
        "October 2026 in Northern Ireland (SR 2025/176 art. 3A(1)). So this is "
        "the share of the fiscal year before the household's date "
        "(gov.dwp.ESA.income.awards_payable): 1 up to 2025-26; in 2026-27, 86 "
        "of 365 days in Great Britain and 178 of 365 in Northern Ireland; and "
        "0 from 2027-28. Art. 3A(1)(b) leaves an award already due to end at "
        "the end of a two-week run-on period (art. 1(2)) to that schedule: "
        "with a migration notice deadline of 22 June 2026 and no claim, SI "
        "2014/1230 reg 46(1)(a) ends the award on 5 July, after the general "
        "date. This annual share does not track deadlines or claim dates, so "
        "it pays every award to the general date. A claim saved for an "
        "appointee has a share of 1 in "
        "every year: a couple's claim is saved when either member who reports "
        "the award is saved (esa_income_appointee_saving), and saving a member "
        "who reports nothing saves nothing. esa_income pays each claim for "
        "this share of the year, and esa_income_report_closed ends its reports "
        "in a year where it is 0. A contributory allowance continues as new "
        "style ESA (esa_contrib)."
    )
    definition_period = YEAR
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/uksi/2025/1148/article/3A",
        "https://www.legislation.gov.uk/nisr/2025/176/article/3A",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/46",
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
        # Art. 3A(2) saves an award for an appointee in every year. The
        # claimant's and partner's award is one award, saved if either of
        # them reports it and is saved; another member's is their own.
        reports_saved = (person("esa_income_reported", period) > 0) & person(
            "esa_income_appointee_saving", period
        )
        couple = person("is_claimant_or_partner", period)
        saved = where(couple, person.benunit.any(couple & reports_saved), reports_saved)
        return where(saved, 1, share)
