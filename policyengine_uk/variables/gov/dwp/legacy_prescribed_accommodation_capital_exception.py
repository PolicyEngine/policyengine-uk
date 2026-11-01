from policyengine_uk.model_api import *


class legacy_prescribed_accommodation_capital_exception(Variable):
    value_type = bool
    entity = BenUnit
    label = "Legacy benefit prescribed accommodation capital tariff exception"
    definition_period = YEAR
    default_value = False
    documentation = (
        "True where the claimant lives permanently in prescribed accommodation "
        "for the capital tariff of Income Support, income-based JSA and "
        "income-related ESA (GB: IS Regs 1987 reg 53(1B)-(1C), JSA Regs 1996 reg "
        "116(1B)-(1C), ESA Regs 2008 reg 118(3)-(4); NI: the same regulations of "
        "SR 1987/459, SR 1996/198 and SR 2008/280). True sets the lower "
        "threshold to £10,000 instead of £6,000. "
        "Assess the claimant's own stay: a partner who lives in a home does not "
        "make the claimant qualify. "
        "In Great Britain the places are a care home, an independent hospital, "
        "an Abbeyfield Home, and Polish Resettlement Act 1947 accommodation "
        "where the claimant requires personal care by reason of old age, "
        "disablement, past or present dependence on alcohol or drugs, past or "
        "present mental disorder or a terminal illness, and receives that care "
        "there. In Northern Ireland they are a residential care home, a nursing "
        "home, an independent hospital and an Abbeyfield Home. "
        "A claimant who is away still counts as living there permanently: away "
        "from a home or hospital for up to 13 weeks (52 weeks for a claimant "
        "over pensionable age under IS and ESA), or away from Polish "
        "Resettlement Act accommodation while the claimant intends, with the "
        "manager's agreement, to return in due course, which has no fixed "
        "limit. "
        "Assess the rules in force for the year and jurisdiction modelled. "
        "Housing Benefit prescribes different circumstances "
        "(housing_benefit_residential_capital_exception), and neither input sets "
        "the other. "
        "Other members who claim in their own right use the benefit unit's "
        "tariff income, so this input sets their threshold too; the model does "
        "not assess their own stay or divide capital between claims. "
        "No dataset supplies this input. It defaults to false, which keeps the "
        "£6,000 threshold and may understate these benefits for qualifying "
        "residents. It does not change eligibility, how capital is valued or "
        "the upper capital limit."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/53",
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/116",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/118",
        "https://www.legislation.gov.uk/nisr/1996/93/regulation/11/made",
        "https://www.legislation.gov.uk/nisr/1996/356/regulation/10/made",
        "https://www.legislation.gov.uk/nisr/2005/458/schedule/1/made",
        "https://www.legislation.gov.uk/nisr/2005/458/schedule/3/made",
        "https://www.legislation.gov.uk/nisr/2008/280/regulation/118",
    )
