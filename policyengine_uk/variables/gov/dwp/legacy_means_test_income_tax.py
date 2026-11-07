from policyengine_uk.model_api import *
from policyengine_uk.utils.legacy_means_test_tax import legacy_means_test_tax_split


class legacy_means_test_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on income the legacy means tests count, by Step 4 component"
    documentation = (
        "The part of the person's income tax that Step 4 of Income Tax Act "
        "2007 s.23 calculates on the income the legacy means tests take into "
        "account, less that income's share of the Step 6 tax reductions. The "
        "tests do not deduct it directly: "
        "legacy_means_test_uncounted_income_tax_without_earnings reads it on "
        "a branch where nobody has employed earnings or self-employment "
        "income, and takes the rest of the pre-charge tax there as the tax on "
        "uncounted income, which legacy_means_test_deducted_income_tax leaves "
        "out. Income Support, Housing Benefit, Pension Credit and council tax "
        "reduction treat savings interest, dividends and property income as "
        "capital, not income, so the counted income here is the person's "
        "other income: earned_income_tax, which covers earnings, pensions and "
        "taxable benefits, and rent_a_room_income_tax, the tax on taxable "
        "rent from boarders, lodgers and sub-tenants in the home. The tests "
        "count that rent as income (HB Regs 2006 Sch 5 paras 22 and 42; HB "
        "(SPC) Regs 2006 reg 29(1)(p) and (v); SPC Regs 2002 reg 15(5)(e) and "
        "(i)), so its tax moves from the property income tax on the capital "
        "side to the counted side. Its share of the Step 6 reductions (the married "
        "couple's allowance, other tax credits, the residential finance-cost "
        "reduction and the Pension Tax Allowance) follows two rules. Most "
        "reductions are not tied to any income: s.27 orders them only to "
        "give the greatest reduction in liability. Two are: foreign tax "
        "credit relief reduces the tax on the income the foreign tax was paid "
        "on (Taxation (International and Other Provisions) Act 2010 ss.18(2) "
        "and 36), and the residential finance-cost reduction is given on at "
        "most the property business's profits, plus any current-year estate "
        "amounts and within the adjusted total income limit (Income Tax "
        "(Trading and Other Income) Act 2005 ss.274A and 274AA). The "
        "finance-cost reduction (property_finance_cost_relief) therefore "
        "comes off the tax on property income first. As a stated convention, "
        "it comes off only the property income tax left on the capital side "
        "(property_income_tax less rent_a_room_income_tax), so the capital "
        "side never goes negative; any excess joins the reductions shared in "
        "proportion to the Step 4 tax. The model's "
        "other_tax_credits input mixes foreign tax credit relief with other "
        "reductions (venture capital trust, enterprise investment and "
        "maintenance relief, among others) and records no source, so those "
        "reductions, and the Pension Tax Allowance, are shared in proportion "
        "to the Step 4 tax on each kind of income, as a stated convention. A "
        "credit for foreign tax on rent is therefore partly attributed to "
        "counted income. Step 7 charges, such as the High Income Child "
        "Benefit Charge, the pension annual allowance charge (s.30) and the "
        "winter fuel payment charge, are not tax calculated on any of this "
        "income, so none is included. The result is "
        "income_tax_before_winter_fuel_payment_charge less the tax attributed "
        "to capital and the other charges, floored at nil, so a supplied "
        "value of the pre-charge tax flows through; if it differs from the "
        "tax the components imply, the difference falls on the tax on "
        "counted income."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/33",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/17",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/27",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/30",
        "https://www.legislation.gov.uk/ukpga/2010/8/section/18",
        "https://www.legislation.gov.uk/ukpga/2010/8/section/36",
        "https://www.legislation.gov.uk/ukpga/2005/5/section/274A",
        "https://www.legislation.gov.uk/ukpga/2005/5/section/274AA",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/22",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/42",
    ]

    def formula(person, period, parameters):
        # Step 4 tax and Step 6 reductions, split between counted income and
        # income from capital (see legacy_means_test_tax_split).
        split = legacy_means_test_tax_split(person, period)
        # Step 7 charges other than the winter fuel payment charge, which the
        # starting value below already leaves out.
        charges = person("income_tax_charges", period)
        # Starting from the income tax the means tests deduct keeps any
        # supplied value: the result is the tax on counted income less its
        # share of reductions whenever that tax is calculated.
        return max_(
            0,
            person("income_tax_before_winter_fuel_payment_charge", period)
            - split["capital_after_reductions"]
            - charges,
        )
