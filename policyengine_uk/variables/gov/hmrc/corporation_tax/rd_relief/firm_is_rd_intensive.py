from policyengine_uk.model_api import *


class firm_is_rd_intensive(Variable):
    value_type = bool
    entity = Firm
    label = "Firm is R&D intensive"
    documentation = (
        "Whether the firm's R&D intensity meets the threshold for the R&D "
        "intensive regime (section 1045ZA of the Corporation Tax Act 2009). "
        "The grace period for a firm that met the test the year before is not "
        "modelled."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2009/4/part/13/chapter/2"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax.rd_relief.sme
        return firm("firm_rd_intensity", period) >= p.intensity_threshold
