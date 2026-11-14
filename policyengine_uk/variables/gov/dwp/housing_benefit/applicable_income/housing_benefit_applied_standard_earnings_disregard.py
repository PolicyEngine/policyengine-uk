from policyengine_uk.model_api import *


class housing_benefit_applied_standard_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit applied standard earnings disregard"
    documentation = (
        "Standard earnings disregard after any permitted-work replacement, "
        "before the separate additional and accommodation amounts. A positive "
        "pre-assessed permitted-work amount replaces the selected standard, "
        "except that a lone parent keeps a higher selected amount. The result "
        "is capped at net earnings. Both the general and savings-credit-only "
        "income calculations use this amount so that the additional disregard "
        "excludes every part of the applied standard."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/10A",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4/paragraph/5A",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5/paragraph/10A",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5/paragraph/5A",
    )

    def formula(benunit, period, parameters):
        net_earnings = max_(benunit("housing_benefit_net_earnings", period), 0)
        # Working age Sch 4 paras 3, 4, 7 and 10; pension age Sch 4 paras 2,
        # 4, 5 and 7. Other full-amount £20 routes are pre-assessed
        # (housing_benefit_special_earnings_disregard_eligible).
        standard = benunit("housing_benefit_special_earnings_disregard", period)
        # Working-age para 10A(2) / pension-age para 5A(2): replace the
        # ordinary amount, except for a higher lone-parent amount. The input
        # already applies the statutory work and partner-allocation limits.
        permitted = max_(benunit("housing_benefit_permitted_work_disregard", period), 0)
        standard = where(
            permitted > 0,
            min_(
                net_earnings,
                max_(permitted, benunit("is_lone_parent", period) * standard),
            ),
            standard,
        )
        return standard
