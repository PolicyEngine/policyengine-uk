from policyengine_uk.model_api import *


def _ordinary_claim_ends_wtc(benunit, period):
    person = benunit.members
    claimant = person("is_uc_single_or_joint_claimant", period)
    at_qualifying_age = person(
        "has_attained_state_pension_credit_qualifying_age", period
    )
    all_claimants_at_qualifying_age = (benunit.sum(claimant) > 0) & benunit.all(
        ~claimant | at_qualifying_age
    )
    return benunit("claims_universal_credit", period) & ~all_claimants_at_qualifying_age


class wtc_terminated_by_universal_credit_claim(Variable):
    value_type = bool
    entity = BenUnit
    definition_period = YEAR
    default_value = False
    label = "Working Tax Credit award ends on a Universal Credit claim"
    documentation = (
        "Whether an ordinary Universal Credit claim ends the claimant's or "
        "joint claimants' Working Tax Credit award, even if no Universal Credit "
        "is payable. The existing annual claim proxy must represent a genuine "
        "claim within the applicable rollout. It does not record claim dates, "
        "deemed or withdrawn claims, or every historical basic condition. "
        "An award remains where the actual single Universal Credit claimant, "
        "or both joint Universal Credit claimants, have attained the qualifying "
        "age for State Pension Credit. A tax-credit partner who cannot join "
        "the Universal Credit claim is not included in this age test "
        "(Universal Credit Regulations 2013 reg 3(3)). Before "
        "25 July 2022 an ordinary claim first had to satisfy the basic "
        "conditions; from that date SI 2014/1230 reg 8(2B) expressly excludes "
        "these claimants. A protected mixed-age Pension Credit route alone "
        "does not exclude a claim. The Great Britain rule starts on 16 June "
        "2014; Northern Ireland's first staged operation starts on "
        "27 September 2017. YEAR formulas select at the period start, so a "
        "January-start transitional year retains the earlier rule. This is "
        "not a claim-date or postcode-level rollout model."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/1/made",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        "https://www.legislation.gov.uk/uksi/2022/752/regulation/5/made",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/6",
        "https://www.legislation.gov.uk/nisr/2017/190/article/4/made",
    )

    def formula_2014_06_16(benunit, period, parameters):
        country = benunit.members.household("country", period)
        in_northern_ireland = benunit.any(
            country == country.possible_values.NORTHERN_IRELAND
        )
        return _ordinary_claim_ends_wtc(benunit, period) & ~in_northern_ireland

    def formula_2017_09_27(benunit, period, parameters):
        return _ordinary_claim_ends_wtc(benunit, period)
