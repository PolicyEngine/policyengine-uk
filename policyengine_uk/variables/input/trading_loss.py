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
        "(ITA 2007 s.64, within the s.24A cap); Class 4 NICs deduct it from "
        "trading profits only (SSCBA 1992 Sch 2 para 3); tax credits deduct it "
        "from the claimants' income (SI 2002/2006 reg 3(1) Step 4); means-tested "
        "benefits never offset it against other earnings; HBAI household income "
        "counts it as negative income. Losses brought forward from earlier "
        "years go in loss_relief."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.per_capita.mixed_income"
    reference = dict(
        title="Income Tax Act 2007 s. 64",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/64",
    )
