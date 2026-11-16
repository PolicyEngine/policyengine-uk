"""How the legacy means tests split a person's Step 4 tax and Step 6 reductions.

``legacy_means_test_income_tax`` and ``rent_a_room_income_tax_after_reductions``
both read this split, so the two cannot share the reductions differently.
"""

import numpy as np

from policyengine_uk.model_api import add, max_, min_


def legacy_means_test_tax_split(person, period):
    """Split the Step 4 tax and Step 6 reductions between counted income and
    income from capital.

    Counted income carries the tax on earnings, pensions and taxable benefits
    (``earned_income_tax``) and the tax on taxable rent-a-room income
    (``rent_a_room_income_tax``). Income from capital carries the tax on
    savings, dividends and the rest of property income. The residential
    finance-cost reduction comes off the tax on property income left on the
    capital side, and no further: any excess joins the general reductions,
    which the formula shares in proportion to the Step 4 tax left on each side.
    """
    rent_a_room_tax = person("rent_a_room_income_tax", period)
    property_tax = person("property_income_tax", period)
    counted = person("earned_income_tax", period) + rent_a_room_tax
    capital_property_tax = max_(0, property_tax - rent_a_room_tax)
    capital = (
        add(person, period, ["savings_income_tax", "dividend_income_tax"])
        + capital_property_tax
    )
    before_reductions = counted + capital
    reductions = min_(person("income_tax_reductions", period), before_reductions)
    finance_cost_relief = min_(
        person("property_finance_cost_relief", period),
        min_(capital_property_tax, reductions),
    )
    general_reductions = reductions - finance_cost_relief
    capital_after_relief = capital - finance_cost_relief
    tax_after_relief = before_reductions - finance_cost_relief

    def share(tax):
        return np.divide(
            tax,
            tax_after_relief,
            out=np.zeros_like(tax_after_relief, dtype=float),
            where=tax_after_relief > 0,
        )

    return dict(
        rent_a_room_tax=rent_a_room_tax,
        counted=counted,
        capital=capital,
        before_reductions=before_reductions,
        reductions=reductions,
        finance_cost_relief=finance_cost_relief,
        general_reductions=general_reductions,
        capital_after_relief=capital_after_relief,
        capital_after_reductions=capital_after_relief
        - general_reductions * share(capital_after_relief),
        rent_a_room_after_reductions=rent_a_room_tax
        - general_reductions * share(rent_a_room_tax),
    )
