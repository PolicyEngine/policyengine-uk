from policyengine_uk.model_api import *


class ni_class_4_losses_brought_forward(Variable):
    value_type = float
    entity = Person
    label = "Trading losses brought forward for Class 4"
    documentation = (
        "Trading losses from earlier years not yet deducted from Class 4 "
        "profits, equal to the previous year's "
        "ni_class_4_losses_carried_forward. By default, losses are carried "
        "forward from the first year a trading_loss is known for, however "
        "many years back. Set this for a year to supply the unrelieved "
        "losses from before it; later years then build on that balance. "
        "trading_loss carries into later years that are not set, so set "
        "them to zero for a one-off loss."
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
        supplied = person.get_holder("ni_class_4_losses_brought_forward")
        earlier_years = [
            known_period.start.year
            for holder in (person.get_holder("trading_loss"), supplied)
            for known_period in holder.get_known_periods()
            if known_period.start < period.start
        ]
        brought_forward = person.empty_array()
        if not earlier_years:
            # No loss can be known for any earlier year.
            return brought_forward
        # Run the carry-forward year by year from the first year a loss is
        # known for: each year's losses are deducted from that year's
        # profits and the rest carried to the next (ITA 2007 s. 84). A loop
        # rather than a formula on the previous year, which the engine would
        # cut off as a spiral after ten years.
        branch_name = person.simulation.branch_name
        for years_back in range(period.start.year - min(earlier_years), 0, -1):
            year = period.offset(-years_back, "year")
            balance = supplied.get_array(year, branch_name)
            if balance is not None:
                brought_forward = balance
            losses = max_(person("trading_loss", year), 0) + max_(brought_forward, 0)
            profits = person("ni_class_4_profits_before_losses", year)
            brought_forward = losses - min_(losses, profits)
        return brought_forward
