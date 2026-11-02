from policyengine_uk.model_api import *


class pension_contributions_via_salary_sacrifice_pre_2015(Variable):
    value_type = float
    entity = Person
    label = "Pension salary sacrifice under arrangements before 9 July 2015"
    documentation = (
        "The annual portion of actual pension salary or bonus sacrifice "
        "attributable to arrangements made before 9 July 2015. Excluded from the annual "
        "allowance threshold-income addback, limited to full sacrifice before "
        "the NICs exemption cap. "
        "Defaults to zero because survey arrangement dates are unobserved."
    )
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.average_earnings"
    reference = "https://www.legislation.gov.uk/ukpga/2004/12/section/228ZA/6"
