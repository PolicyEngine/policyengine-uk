from policyengine_uk.model_api import *
from policyengine_uk.utils.pensions import trading_profits_before_losses
from policyengine_uk.utils.supplied_inputs import supplied_input, supplied_input_periods


class loss_relief(Variable):
    value_type = float
    entity = Person
    label = "Unrelieved trade losses at the start of the year"
    reference = dict(
        title="Income Tax Act 2007 s. 83",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/83",
    )
    documentation = (
        "Opening unrelieved losses available against profits of the same "
        "continuing trade, or a caller-preassessed eligible trade pool "
        "(ITA 2007 ss.83-84). The model assumes a carry-forward claim and "
        "tracks supplied-year losses after actual general-income relief and "
        "prior losses absorbed by trading profits. This stock can exceed "
        "this year's deduction, which cannot reduce trading profits below "
        "zero or reduce other income. An explicit input, including zero, "
        "overrides the opening stock for that year and reconciles external "
        "relief or earlier history. Class 4 tracks a separate loss balance."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

    def formula(person, period, parameters):
        earlier_years = [
            supplied_period.start.year
            for variable in ("trading_loss", "loss_relief")
            for supplied_period in supplied_input_periods(person, variable)
            if supplied_period.start.year < period.start.year
        ]
        if not earlier_years:
            return person.empty_array()

        balance = person.empty_array()
        for years_back in range(period.start.year - min(earlier_years), 0, -1):
            year = period.offset(-years_back, "year")
            # Resolve each opening balance before the year's allowance reads
            # it. Earlier years' dependencies are already ordinarily cached;
            # this also respects an explicitly supplied opening-stock reset.
            opening = max_(0, person("loss_relief", year))
            profits = trading_profits_before_losses(
                person, year, parameters(year).gov.hmrc
            )
            absorbed = min_(opening, profits)
            current_loss = supplied_input(person, "trading_loss", year)
            if current_loss is None:
                current_loss = person.empty_array()
            eligible_loss = where(
                person("trading_allowance_deduction", year) > 0,
                0,
                max_(0, current_loss),
            )
            used_against_general_income = person(
                "trade_loss_relief_against_general_income", year
            )
            balance = (
                opening
                - absorbed
                + max_(0, eligible_loss - used_against_general_income)
            )
        return balance
