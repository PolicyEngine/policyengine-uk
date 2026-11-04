from policyengine_uk.model_api import *


class guardians_allowance(Variable):
    value_type = float
    entity = Person
    label = "Guardian's Allowance"
    documentation = (
        "Guardian's Allowance cash received by this person. Calculated "
        "full-rate cash is for an entitled person who is also the cash "
        "recipient. Authoritative direct cash, including zero, represents "
        "a distinct lawful payee or an exceptional, adjusted or mixed-rate "
        "payment; record legal entitlement separately on its holder. A "
        "direct input uses the ordinary whole-array Core override, without "
        "a per-cell reported/calculated merge. This payment must be disjoint "
        "from miscellaneous or other income supplied separately."
    )
    definition_period = YEAR
    unit = GBP
    category = BENEFIT
    default_value = 0
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/77",
        "https://www.legislation.gov.uk/ukpga/1992/7/section/77",
        "https://www.legislation.gov.uk/ukpga/2003/1/section/677",
    )

    def formula(person, period, parameters):
        entitled = person("is_entitled_to_guardians_allowance", period)
        child_weeks = person("guardians_allowance_full_rate_child_weeks", period)
        payable_child_weeks = where(entitled, max_(child_weeks, 0), 0)
        if not np.any(payable_child_weeks > 0):
            return payable_child_weeks
        # The explicit verification window is not a historical rate assumption.
        if not 2024 <= period.start.year <= 2026:
            raise ValueError(
                "Guardian's Allowance computed cash is supported only for "
                "2024–2026; supply authoritative direct cash for other years."
            )
        rate = parameters(period).gov.hmrc.guardians_allowance.weekly_rate
        return rate * payable_child_weeks
