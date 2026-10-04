from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import (
    supplied_input,
    supplied_input_periods,
)


class ni_class_4_losses_brought_forward(Variable):
    value_type = float
    entity = Person
    label = "Trading losses brought forward for Class 4"
    documentation = (
        "Trading losses from earlier years not yet deducted from Class 4 "
        "profits, equal to the previous year's "
        "ni_class_4_losses_carried_forward. By default, losses are carried "
        "forward from the first year a trading_loss is supplied for, however "
        "many years back. Set this for a year to supply the unrelieved "
        "losses from before it; later years then build on that balance. "
        "Each loss counts once, in the year it is supplied for "
        "(ni_class_4_trading_loss), so a one-off loss needs no zeros in "
        "later years."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992, Sch. 2 para. 3(1)(c) and (4)(b)",
            href="https://www.legislation.gov.uk/ukpga/1992/4/schedule/2/paragraph/3",
        ),
        dict(
            title="Income Tax Act 2007, ss. 83 and 84",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/84",
        ),
    ]

    def formula(person, period, parameters):
        # Only supplied values count. The engine also stores values it fills
        # in (an input carried into a later year, or a cached calculation),
        # and whether those exist depends on what was calculated first.
        earlier_years = [
            supplied_period.start.year
            for variable in (
                "trading_loss",
                "ni_class_4_trading_loss",
                "ni_class_4_losses_brought_forward",
            )
            for supplied_period in supplied_input_periods(person, variable)
            if supplied_period.start < period.start
        ]
        brought_forward = person.empty_array()
        if not earlier_years:
            # No loss is supplied for any earlier year.
            return brought_forward
        # Run the carry-forward year by year from the first year a loss is
        # supplied for: each year's losses are deducted from that year's
        # profits and the rest carried to the next (ITA 2007 s. 84). A loop
        # rather than a formula on the previous year, which the engine would
        # cut off as a spiral after ten years.
        for years_back in range(period.start.year - min(earlier_years), 0, -1):
            year = period.offset(-years_back, "year")
            balance = supplied_input(person, "ni_class_4_losses_brought_forward", year)
            if balance is not None:
                brought_forward = max_(balance, 0)
            losses = person("ni_class_4_trading_loss", year) + brought_forward
            profits = person("ni_class_4_profits_before_losses", year)
            brought_forward = losses - min_(losses, profits)
        return brought_forward
