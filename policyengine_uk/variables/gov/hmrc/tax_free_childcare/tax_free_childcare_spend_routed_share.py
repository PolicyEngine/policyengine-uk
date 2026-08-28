from policyengine_uk.model_api import *


class tax_free_childcare_spend_routed_share(Variable):
    value_type = float
    entity = Person
    label = "share of a child's childcare spending routed through a Tax-Free Childcare account"
    documentation = (
        "Share of the childcare spending recorded against this child that is "
        "paid through a Tax-Free Childcare account, and so attracts the "
        "government top-up. Per child, because a Tax-Free Childcare account is "
        "held for one child only (Childcare Payments Act 2014 section 15(2)) "
        "and both childcare_expenses and tax_free_childcare are person-level. "
        "Defaults to 1 — a neutral all-spend-routed assumption, not a statutory "
        "requirement — so a household calculation returns the statutory amount. "
        "The dataset build may supply an HMRC-derived account-activity "
        "duration proxy rather than an observed routed-expenditure share; see "
        "policyengine-uk-data.\n\n"
        "Denominator: the share is measured ACROSS THE ELIGIBLE PERIOD, not "
        "across the whole year. tax_free_childcare already multiplies annual "
        "spending by the eligible-period fraction, so a whole-year share would "
        "discount the same months twice: a family eligible for six months that "
        "routes spending in three of them has a whole-year share of 3/12, and "
        "annual_spend * 0.5 * 0.25 is half the amount actually routed. The "
        "eligible-period share is 3/6, and annual_spend * 0.5 * 0.5 is right."
    )
    definition_period = YEAR
    unit = "/1"
    default_value = 1
    reference = "https://www.legislation.gov.uk/ukpga/2014/28/section/15"
