from policyengine_uk.model_api import *


class firm_full_expensing_balancing_charge(Variable):
    value_type = float
    entity = Firm
    label = "Firm full expensing balancing charge"
    documentation = (
        "Balancing charge on a company's disposal of main-rate plant and "
        "machinery on which it claimed full expensing: the relevant "
        "proportion of the disposal value, charged in the year of disposal "
        "outside the main pool and in addition to any pool balancing charge "
        "(section 59A of the Capital Allowances Act 2001). Capped at the main "
        "pool disposal proceeds, which include these proceeds. Companies "
        "only, in years when full expensing is available."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2001/2/section/59A",
        "https://www.legislation.gov.uk/ukpga/2001/2/section/45S",
    )

    def formula(firm, period, parameters):
        rate = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.first_year_allowances.full_expensing_rate
        legal_form = firm("firm_legal_form", period)
        is_company = legal_form == legal_form.possible_values.COMPANY
        # The proceeds are part of the main pool disposal proceeds.
        proceeds = min_(
            max_(firm("firm_disposal_proceeds_full_expensing", period), 0),
            max_(firm("firm_disposal_proceeds_main_pool", period), 0),
        )
        return where(is_company & (rate > 0), proceeds, 0)
