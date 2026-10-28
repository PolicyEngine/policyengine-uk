from policyengine_uk.model_api import *


class income_support_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Income Support earnings disregard"
    documentation = (
        "Earnings disregarded in the Income Support means test under Schedule "
        "8 to the Income Support (General) Regulations 1987: £20 a week for a "
        "lone parent (paragraph 5), £10 for a couple (paragraph 6) and £5 "
        "otherwise (paragraph 9). Regulations 36(2) and 38(2) take these sums "
        "from net earnings, so the disregard is capped at the claimant's and "
        "partner's net earnings (income_support_net_earnings) and never "
        "reduces statutory pay, pensions, benefits or other income. A couple "
        "share one £10 (paragraph 6(a)). Not modelled: the £20 disregards for "
        "a disability premium (paragraph 4), a carer premium (paragraphs 6A "
        "and 6B) and the listed part-time occupations (paragraphs 7 and 8), "
        "and the full disregards of paragraphs 1 to 3 for employment that has "
        "ended."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/8",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/36",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/38",
    )

    def formula(benunit, period, parameters):
        mt = parameters(period).gov.dwp.income_support.means_test
        # Schedule 8 paras 5, 6 and 9 use mutually exclusive claimant types.
        weekly = (
            benunit("is_single_person", period) * mt.income_disregard_single
            + benunit("is_couple", period) * mt.income_disregard_couple
            + benunit("is_lone_parent", period) * mt.income_disregard_lone_parent
        )
        return min_(
            weekly * WEEKS_IN_YEAR, benunit("income_support_net_earnings", period)
        )
