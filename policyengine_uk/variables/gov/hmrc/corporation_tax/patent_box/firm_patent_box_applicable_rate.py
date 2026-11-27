from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_patent_box_applicable_rate(Variable):
    value_type = float
    entity = Firm
    label = "Firm Patent Box applicable rate"
    documentation = (
        "The rate in the Patent Box formula: the main rate before 1 April "
        "2023 (MR), and from then the small profits rate where the company "
        "is charged at it and the main rate otherwise (AR, F(No.2)A 2023 "
        "s.11). Following HMRC's CIRD201020, the small profits test uses "
        "profits before the Patent Box deduction. As a model simplification, "
        "not HMRC's, it also ignores group relief and carried-forward losses "
        "(firm_profits_before_patent_box plus exempt distributions), so a "
        "company brought under the lower limit only by those reliefs takes "
        "the main rate and its deduction is overstated (15/25 instead of "
        "9/19 of relevant IP profits)."
    )
    definition_period = YEAR
    unit = "/1"
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2010/4/section/357A",
        "https://www.legislation.gov.uk/ukpga/2023/30/section/11",
        "https://www.gov.uk/hmrc-internal-manuals/corporate-intangibles-research-and-development-manual/cird201020",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax
        if not p.small_profits_rate_applies:
            return np.full(firm.count, p.main_rate)
        augmented = max_(firm("firm_profits_before_patent_box", period), 0) + firm(
            "firm_exempt_distributions", period
        )
        small = (augmented <= firm("firm_corporation_tax_lower_limit", period)) & ~firm(
            "firm_small_profits_rate_excluded", period
        )
        return where(small, p.small_profits_rate, p.main_rate)
