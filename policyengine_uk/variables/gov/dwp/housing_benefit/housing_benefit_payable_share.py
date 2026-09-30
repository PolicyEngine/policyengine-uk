from policyengine_uk.model_api import *


class housing_benefit_payable_share(Variable):
    value_type = float
    entity = BenUnit
    label = "Share of the year Housing Benefit is payable"
    documentation = (
        "Share of the year for which this family's Housing Benefit award stays "
        "payable. Working-age awards outside specified and temporary "
        "accommodation were abolished from 1 July 2026 in Great Britain and "
        "1 October 2026 in Northern Ireland, so for a family with no member "
        "over State Pension age this is the share of the year before that "
        "date. Families with a member over State Pension age keep their award "
        "(the pension-age and mixed-age savings), so theirs is 1."
    )
    definition_period = YEAR
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/uksi/2025/1148/article/7",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/6A",
        "https://www.legislation.gov.uk/nisr/2025/176/article/7",
    )

    def formula(benunit, period, parameters):
        payable = parameters(period).gov.dwp.housing_benefit.working_age_awards_payable
        country = benunit.household("country", period)
        working_age_share = where(
            country == country.possible_values.NORTHERN_IRELAND,
            payable.northern_ireland,
            payable.great_britain,
        )
        # SI 2025/1148 art. 7(4)(a) saves claimants within SI 2014/1230
        # reg 6A(2)-(5). Reg 6A(4) (pension age) and 6A(5) (mixed-age couples
        # saved by SI 2019/37 art. 4) are the savings the model can see: any
        # member over State Pension age keeps the award running. In law a
        # mixed-age couple is saved only if the older member claims under the
        # pension-age regulations and the couple has been entitled since
        # 14 May 2019, which the data cannot show. Specified and temporary
        # accommodation (reg 6A(2)), prisoners (art. 7(2)) and the income-
        # related ESA appointee saving (art. 7(4)(b)) have no inputs.
        any_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
        return where(any_over_SP_age, 1, working_age_share)
