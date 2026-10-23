from policyengine_uk.model_api import *


class carer_support_payment_pre_overlap(Variable):
    value_type = float
    entity = Person
    label = "Carer Support Payment before the overlapping-benefit reduction"
    documentation = (
        "The Carer Support Payment component a carer in Scotland is entitled "
        "to before regulation 16(2) of the Carer Support Payment Regulations "
        "reduces it by an overlapping benefit. A carer whose payment is "
        "reduced to £0 keeps this underlying entitlement. "
        "carer_support_payment is the amount given. The earnings condition uses "
        "the existing annual Carer's Allowance net-earnings reader, spread "
        "evenly over 52 weeks. This approximates constant earnings; it cannot "
        "resolve the award-week or, from 16 November 2025, preceding-award-week "
        "assessment for varying earnings. The reader's standard-code PAYE and "
        "unrepresented care-charge/disregard assumptions also apply."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/asp/2018/9/part/4",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/3",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/4",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/16",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/14",
        "https://www.legislation.gov.uk/ssi/2023/302/schedule/2/paragraph/4",
    )

    def formula(person, period, parameters):
        in_scotland = person.household("country", period).decode_to_str() == "SCOTLAND"
        csp_in_effect = period.start.year >= 2025
        if not csp_in_effect:
            return person.empty_array()
        csp = parameters(period).gov.social_security_scotland.carer_support_payment
        meets_age_condition = person("age", period) >= csp.min_age
        weekly_care_hours = person("care_hours", period)
        meets_hours = weekly_care_hours >= csp.min_hours
        receives_ca = person("carers_allowance_reported", period) > 0
        would_claim = person("would_claim_carers_allowance", period)
        earnings = person("carers_allowance_earnings", period)
        # Schedule 2 paragraph 4 disregards an adverse fraction of a penny.
        # The first excluded weekly amount is the limit plus one penny.
        # Compare annual amounts in the reader's dtype so the encoded exact
        # penny boundary is not admitted through scalar/array rounding.
        first_excluded_annual_earnings = np.asarray(
            (csp.earnings_limit + csp.earnings_rounding_precision) * WEEKS_IN_YEAR,
            dtype=earnings.dtype,
        )
        meets_earnings = earnings < first_excluded_annual_earnings
        eligible = (
            in_scotland
            & csp_in_effect
            & (meets_hours | receives_ca)
            & meets_earnings
            & meets_age_condition
            & would_claim
        )
        return eligible * csp.rate * WEEKS_IN_YEAR
