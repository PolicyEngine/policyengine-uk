from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class plastic_packaging_tax(Variable):
    value_type = float
    entity = Firm
    label = "Plastic packaging tax"
    documentation = (
        "Plastic packaging tax on the firm's chargeable plastic packaging "
        "components, those with less than 30% recycled plastic: the rate "
        "per tonne, part tonnes pro rata (Finance Act 2021 ss.43 and 45), "
        "from 1 April 2022. A firm neither registered nor liable to "
        "register pays nothing (s.43(2A)); it is liable to register where "
        "its finished components, whatever their recycled content, reach "
        "10 tonnes (s.55), applied here to the year. The rate is read at 30 "
        "April, so the rate from 1 April applies to the whole year. Not "
        "modelled: the exemptions in s.52, the credits for exported or "
        "converted packaging, and the mass balance approach."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Finance Act 2021 Part 2",
            href="https://www.legislation.gov.uk/ukpga/2021/26/part/2",
        ),
        dict(
            title="Finance Act 2021 s.43",
            href="https://www.legislation.gov.uk/ukpga/2021/26/section/43",
        ),
        dict(
            title="Finance Act 2021 s.55",
            href="https://www.legislation.gov.uk/ukpga/2021/26/section/55",
        ),
    ]

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.plastic_packaging_tax
        chargeable = max_(firm("firm_plastic_packaging_tonnes_chargeable", period), 0)
        total = max_(firm("firm_plastic_packaging_tonnes_total", period), chargeable)
        liable = total >= p.registration_threshold
        return where(liable, chargeable * p.rate, 0)
