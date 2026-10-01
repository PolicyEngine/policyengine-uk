from policyengine_uk.model_api import *
import pandas as pd
import warnings
from policyengine_core.model_api import *

warnings.filterwarnings("ignore")


class LHA_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable amount for LHA"
    documentation = (
        "Rent eligible for Housing Benefit where the Local Housing Allowance "
        "applies: the lower of the rent and the Housing Benefit LHA rate. "
        "Where the rent pays for meals, the rent officer route applies "
        "instead and the fixed meals amount is deducted from the maximum "
        "rent; the model takes the rent less that amount, capped at the LHA "
        "rate, which stands in for the rent officer's determination."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/12D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13C",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
    )

    def formula(benunit, period, parameters):
        # HB Regs 2006 regs 12D(2)(a) and 13D(5): the maximum rent (LHA) is
        # the LHA rate or, if lower, the cap rent. A rent officer finding
        # that a substantial part of the rent is for board and attendance
        # takes the case off the LHA (reg 13C(5)(e)); the maximum rent then
        # has the Sch 1 para 2 amount for meals deducted (reg 13(13)).
        rent = max_(
            0,
            benunit("benunit_rent", period)
            - benunit("housing_benefit_meals_deduction", period),
        )
        cap = benunit("housing_benefit_LHA_rate", period)
        return min_(rent, cap)
