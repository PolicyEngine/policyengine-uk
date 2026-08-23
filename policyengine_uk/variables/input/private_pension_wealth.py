from policyengine_uk.model_api import *


class private_pension_wealth(Variable):
    label = "private pension wealth"
    documentation = (
        "Value of the household's private (non-state) pension rights other than "
        "current-employment defined benefit entitlements, which the data does "
        "not yet carry: defined contribution pots, additional voluntary "
        "contributions, current personal pensions, retained rights in earlier "
        "occupational and personal schemes (defined benefit and defined "
        "contribution, including drawdown funds), pensions in payment valued as "
        "the capitalised income stream, and pensions expected under a pension "
        "sharing order. Imputed from the Wealth and Assets Survey as total "
        "private pension wealth less the current defined benefit component, "
        "both at the SCAPE discount rate. Datasets built before this column "
        "existed folded it into corporate_wealth. The value of a right to "
        "receive a pension under an occupational or personal pension scheme is "
        "disregarded as capital in every means test the model runs (see the "
        "capital sources parameters of each benefit for the paragraph), so this "
        "variable is not a capital source anywhere; pension income actually "
        "drawn counts through private_pension_income. Not modelled: the "
        "notional income rule for claimants over State Pension Credit age with "
        "undrawn money purchase pots, and the capital treatment of withdrawn "
        "lump sums."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
    default_value = 0
