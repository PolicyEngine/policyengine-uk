from policyengine_uk.model_api import *


class housing_benefit_payable_share(Variable):
    value_type = float
    entity = BenUnit
    label = "Share of the year Housing Benefit is payable"
    documentation = (
        "Share of the year for which this family's Housing Benefit award stays "
        "payable. Unprotected working-age awards outside specified and temporary "
        "accommodation were abolished from 1 July 2026 in Great Britain and "
        "1 October 2026 in Northern Ireland, so for a family with no member "
        "over State Pension age this is the share of the year before that "
        "date, unless in_specified_or_temporary_accommodation is True. "
        "That input preserves a share of 1 in every year. Families with a "
        "member over State Pension age also have a share of 1 (the model's "
        "pension-age and protected mixed-age approximation). Other saved "
        "working-age awards are not modelled: qualifying HB claims during the "
        "final UC assessment period on reaching pension-credit age, with "
        "entitlement from reaching that age and the relevant Decisions and "
        "Appeals Schedule 1 paragraph 26 applying (reg 6A(3); NI reg 4A(3)); "
        "income-related "
        "ESA entitlement immediately before abolition with an appointee then, "
        "or a determination in the preceding six months that one was likely "
        "needed (art 7(4)(b) and 3A(2)); and the delayed termination for "
        "claimants excluded from UC immediately before abolition under UC "
        "reg 19(1)(b) or (c), until the day after the last day of that "
        "exclusion (art 7(2)). These need award history, decisions or dates "
        "which no inputs supply."
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
        # Great Britain's date applies everywhere but Northern Ireland,
        # including an unknown country.
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
        # accommodation is supplied explicitly under reg 6A(2) (NI reg 4A(2)).
        # The other savings described in the variable documentation have no
        # inputs for their history and date conditions.
        any_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
        protected_accommodation = benunit(
            "in_specified_or_temporary_accommodation", period
        )
        return where(any_over_SP_age | protected_accommodation, 1, working_age_share)
