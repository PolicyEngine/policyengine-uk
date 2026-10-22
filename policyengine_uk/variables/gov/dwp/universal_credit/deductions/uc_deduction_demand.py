from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.deductions._deduction_amounts import (
    deduction_type_shares,
)


class uc_deduction_demand(Variable):
    label = "UC cash deductions before the award and protected floor limits"
    documentation = (
        "Cash advance and maintenance demands plus the estimated percentage heads. "
        "Ordinary debt obeys the administrative cap; maintenance can exceed it, "
        "but together they obey the statutory ceiling. Only Schedule 6 "
        "paragraph 4(3)-(4) last resort deductions bypass that ceiling. The legacy "
        "third party and government rate shares remain calibration proxies, not "
        "an assertion that every agreement in those categories is percentage based."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2013/380/schedule/6/paragraph/4"

    def formula(benunit, period, parameters):
        law = parameters(period).gov.dwp.universal_credit.deductions
        calibration_cap = parameters(
            period
        ).gov.simulation.uc_deductions.calibration_cap
        _, third_share, government_share = deduction_type_shares(
            benunit, period, parameters
        )
        percentage_share = third_share * (
            not law.abolish.third_party
        ) + government_share * (not law.abolish.government)
        allowance = max_(benunit("uc_standard_allowance", period), 0)
        latent = max_(benunit("uc_latent_deduction_rate", period), 0)
        percentage = min_(latent, calibration_cap) * percentage_share * allowance
        advance = max_(benunit("uc_advance_repayment_amount", period), 0)
        if law.abolish.advance:
            advance = 0
        maintenance = max_(benunit("uc_child_maintenance_deduction_amount", period), 0)
        statutory_limit = law.statutory_cap * allowance
        ordinary = min_(advance + percentage, law.cap * allowance)
        non_exempt = min_(ordinary + maintenance, statutory_limit)
        last_resort = max_(benunit("uc_last_resort_deduction_amount", period), 0)
        return non_exempt + last_resort
