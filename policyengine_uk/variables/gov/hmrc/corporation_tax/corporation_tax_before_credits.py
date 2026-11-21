from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class corporation_tax_before_credits(Variable):
    value_type = float
    entity = Firm
    label = "corporation tax before credits"
    documentation = (
        "Corporation tax on taxable total profits: the small profits rate "
        "where augmented profits do not exceed the lower limit, otherwise the "
        "main rate less marginal relief. Each firm is treated as having an "
        "April-to-March accounting period, so no apportionment between "
        "financial years is needed."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2010/4/section/3",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/18A",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/18B",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax
        taxable = firm("firm_taxable_profit", period)
        main_rate_tax = taxable * p.main_rate
        if not p.small_profits_rate_applies:
            return main_rate_tax
        augmented = firm("firm_augmented_profits", period)
        lower = firm("firm_corporation_tax_lower_limit", period)
        marginal_relief = firm("firm_marginal_relief", period)
        return where(
            augmented <= lower,
            taxable * p.small_profits_rate,
            main_rate_tax - marginal_relief,
        )
