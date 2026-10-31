from policyengine_uk.model_api import *


class trading_loss(Variable):
    value_type = float
    entity = Person
    label = "trading loss"
    documentation = (
        "Losses made in the tax year by the person's trades, professions or "
        "vocations, as a positive amount. Profits of their other trades go in "
        "self_employment_income, which is never negative. Each programme reads "
        "the loss by its own rule: Income Tax deducts it from general income "
        "(ITA 2007 s.64, within the s.24A cap), if ordinary expense treatment "
        "beats the trading allowance for the individual's year; Class 4 NICs "
        "deduct it from "
        "trading profits only (SSCBA 1992 Sch 2 para 3); tax credits deduct it "
        "from the claimants' income (SI 2002/2006 reg 3(1) Step 4); means tests "
        "never set it against employed earnings or other income: UC sets it "
        "against the person's other trades' profits (UC Regs 2013 reg 57(2)), "
        "and HB, CTR, Pension Credit and the legacy benefits not even that (HB "
        "Regs 2006 reg 38(10)); HBAI household income counts it as negative "
        "income. Income Tax tracks unrelieved earlier losses in loss_relief, "
        "under its current-year and same-trade carry-forward claim "
        "conventions; an explicit opening loss_relief overrides that stock. Class 4 "
        "tracks its own unrelieved balance in ni_class_4_losses_brought_forward. "
        "Income Tax and Class 4 count only explicitly supplied loss years "
        "and carry their unused balances forward separately. For a one-off "
        "loss, set subsequent years explicitly to zero for other programmes "
        "that read inherited values of this input."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.per_capita.mixed_income"
    reference = dict(
        title="Income Tax Act 2007 s. 64",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/64",
    )
