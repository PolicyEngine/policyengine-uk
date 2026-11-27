from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_plastic_packaging_tonnes_total(Variable):
    label = "Plastic packaging tonnes for the registration test"
    documentation = (
        "Tonnes of finished plastic packaging components the firm "
        "manufactures in or imports into the UK in the year, whatever their "
        "recycled content, less the exempt components, for the 10 tonne "
        "registration test (Finance Act 2021 s.55). Defaults to the "
        "chargeable tonnes; supply it where the firm also has components "
        "with 30% or more recycled plastic. The test is applied to the "
        "year, not the rolling 12 months or the next 30 days in s.55."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    reference = "https://www.legislation.gov.uk/ukpga/2021/26/section/55"
    adds = ["firm_plastic_packaging_tonnes_chargeable"]
