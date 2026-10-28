from policyengine_uk.model_api import *


class carers_allowance_pre_couple_limit(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance before the couple and overlap restrictions"
    documentation = (
        "The existing age, caring, earnings and take-up calculation before "
        "the same-person couple restriction and overlapping-benefit adjustment. "
        "This candidate amount is not final entitlement or payment."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/ukpga/1992/7/section/70",
    )

    def formula(person, period, parameters):
        in_scotland = person.household("country", period).decode_to_str() == "SCOTLAND"
        csp_replaces_ca = period.start.year >= 2025
        receives_ca = person("carers_allowance_reported", period) > 0
        ca = parameters(period).gov.dwp.carers_allowance
        meets_age_condition = person("age", period) >= ca.min_age
        weekly_care_hours = person("care_hours", period)
        meets_work_condition = weekly_care_hours >= ca.min_hours
        would_claim = person("would_claim_carers_allowance", period)
        # SSCBA 1992 s. 70(1)(b): no allowance for anyone gainfully employed,
        # which reg. 8 of the 1976 Regulations defines by an earnings limit.
        # It applies to reported recipients too.
        gainfully_employed = person(
            "is_gainfully_employed_for_carers_allowance", period
        )
        # Budget 2026 (para 6.13) replaces that cliff edge in England and
        # Wales with a taper: the weekly allowance less taper.rate for each
        # pound of weekly earnings above the limit. A year the taper starts
        # in part pays the tapered amount for the share of its weeks that
        # carers_allowance_share_of_year_payable gives.
        excess = person("carers_allowance_weekly_earnings_above_limit", period)
        tapered = max_(0, ca.rate - ca.earnings_taper.rate * excess)
        share = person("carers_allowance_share_of_year_payable", period)
        weekly = share * where(gainfully_employed, tapered, ca.rate)
        eligible = (
            ~(in_scotland & csp_replaces_ca)
            & (meets_work_condition | receives_ca)
            & would_claim
            & meets_age_condition
        )
        return eligible * weekly * WEEKS_IN_YEAR
