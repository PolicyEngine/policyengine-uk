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
        "Rent eligible for Housing Benefit for a private renter. On the Local "
        "Housing Allowance route it is the lower of the rent (gross, meals "
        "included) and the Housing Benefit LHA rate. Where a rent officer has "
        "found that a substantial part of the rent is for board and "
        "attendance (housing_benefit_board_and_attendance_determination), the "
        "LHA does not apply and the maximum rent is the rent officer's "
        "figure less the fixed amount for meals; the model takes the rent "
        "less that amount, as it has no rent officer determinations."
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
        rent = benunit("benunit_rent", period)
        # HB Regs 2006 regs 12D(2)(a) and 13D(5), (12): the maximum rent
        # (LHA) is the LHA rate or, if lower, the cap rent, which is the
        # gross rent liability.
        lha_route = min_(rent, benunit("housing_benefit_LHA_rate", period))
        # Reg 13C(5)(e): a rent officer finding that a substantial part of
        # the rent is board and attendance takes the case off the LHA; the
        # maximum rent then has the Sch 1 para 2 amount for meals deducted
        # (reg 13(7)).
        rent_officer_route = max_(
            0, rent - benunit("housing_benefit_meals_deduction", period)
        )
        return where(
            benunit("housing_benefit_board_and_attendance_determination", period),
            rent_officer_route,
            lha_route,
        )
