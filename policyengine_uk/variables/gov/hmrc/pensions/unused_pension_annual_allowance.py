from policyengine_uk.model_api import *
from policyengine_uk.utils.pensions import annual_allowance_for_year

# Years of assumed history: the three years whose unused allowance is carried
# forward, and the two before them, whose unused allowance an excess in those
# three years uses first.
HISTORY_YEARS = 5


class unused_pension_annual_allowance(Variable):
    label = "unused pension annual allowance brought forward"
    documentation = (
        "Unused annual allowance from the three previous tax years that is "
        "available for this tax year (FA 2004 s. 228A(5)): the amount by which "
        "each of those years' annual allowance exceeded the total pension "
        "input amount, for years in which the individual was a member of a "
        "registered pension scheme, less any part already used up in an "
        "intervening year (earliest year first). It increases this year's "
        "annual allowance (s. 228A(2)). Supply it where the history is known. "
        "Survey data records no past pension input, so from 2020-21 the "
        "default assumes that in each of the five previous years the input "
        "was this year's times gov.simulation.pensions.prior_year_input_ratio "
        "and the incomes tested for the taper were this year's, each deflated "
        "by average earnings growth, and that a person with pension input "
        "this year was a member in each of those years. Each year's excess "
        "over its allowance uses the unused allowance of the three years "
        "before it, earliest first (s. 228A(7)). Before 2020-21 the default "
        "is nil."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        dict(
            title="Finance Act 2004 s. 228A",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/228A",
        ),
        dict(
            title="HMRC Pensions Tax Manual PTM055100",
            href="https://www.gov.uk/hmrc-internal-manuals/pensions-tax-manual/ptm055100",
        ),
    ]

    def formula_2020(person, period, parameters):
        ratio = parameters(period).gov.simulation.pensions.prior_year_input_ratio
        pension_input = person("pension_contributions_for_annual_allowance", period)
        adjusted_income = person("pension_annual_allowance_adjusted_income", period)
        threshold_income = person("pension_annual_allowance_threshold_income", period)
        # Each earlier year's amounts are this year's over the average
        # earnings growth since then.
        level = {0: 1.0}
        for years_back in range(1, HISTORY_YEARS + 1):
            growth = parameters(
                period.offset(1 - years_back, YEAR)
            ).gov.economic_assumptions.yoy_growth.obr.average_earnings
            level[years_back] = level[years_back - 1] / (1 + growth)
        unused = {}
        for years_back in range(HISTORY_YEARS, 0, -1):
            year = period.offset(-years_back, YEAR)
            scale = level[years_back]
            allowance = annual_allowance_for_year(
                adjusted_income * scale,
                threshold_income * scale,
                parameters(year).gov.hmrc.income_tax.allowances.annual_allowance,
                year.start.year,
            )
            prior_input = ratio * pension_input * scale
            # s. 228A(7): an excess uses the unused allowance of the three
            # years before it, earliest first.
            excess = max_(0, prior_input - allowance)
            for earlier in (years_back + 3, years_back + 2, years_back + 1):
                if earlier in unused:
                    used = min_(unused[earlier], excess)
                    unused[earlier] = unused[earlier] - used
                    excess = excess - used
            unused[years_back] = max_(0, allowance - prior_input)
        # s. 228A(4): a year counts only if the individual was a member of a
        # registered pension scheme then.
        return where(pension_input > 0, unused[1] + unused[2] + unused[3], 0)
