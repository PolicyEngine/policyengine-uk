from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import stored_as_input


def award_reads_no_other_variable(simulation, period):
    """Whether reading universal_credit for this period reads no other
    variable: a reform neutralized it, or an input or a scenario stored its
    value for the period."""
    variable = simulation.tax_benefit_system.get_variable("universal_credit")
    return variable.is_neutralized or stored_as_input(
        simulation.populations["benunit"], "universal_credit", period
    )


class has_uc_award_with_carer_element(Variable):
    value_type = bool
    entity = Person
    label = "has a Universal Credit award with the carer element"
    documentation = (
        "Whether this person has an award of Universal Credit which includes "
        "the carer element (Universal Credit Regulations 2013 reg 29) in "
        "respect of them: the carer condition of the legacy severe disability "
        "premium (HB Regs 2006 Sch 3 para 14(2)(a)(iii) and (b)) and of the "
        "Pension Credit severe disability addition (SPC Regs 2002 Sch I para "
        "1(1) and (4)), through is_cared_for_by_carer_benefit_recipient. "
        "An award needs an amount payable of at least one penny (Welfare "
        "Reform Act 2012 s.5(1)(b) and (2)(b); UC Regs 2013 reg 17), so the "
        "model counts a claimant in respect of whom the award includes the "
        "carer element (uc_carer_element_included_for_claimant) only where "
        "the family's award before the benefit cap "
        "(universal_credit_pre_benefit_cap) comes to more than nil. That "
        "award comes to nil where income tapers it to nil, after any "
        "non-dependant deduction and with the work allowance that the "
        "housing costs element sets, and where the family takes Tax-Free "
        "Childcare instead (forgoes_universal_credit_for_tax_free_childcare). "
        "The model reads the award before the cap, not universal_credit, "
        "because the benefit cap reads Child Tax Credit, whose income reads "
        "Pension Credit, whose addition reads this variable. The two agree "
        "for an award that includes the carer element: DWP exempts it from "
        "the cap (UC Regs 2013 reg 83(1)(j)), and debt deductions leave at "
        "least one penny payable. The housing costs element reads the "
        "non-dependant deduction. Its exemption for a non-dependant family "
        "on Pension Credit (uc_non_dep_receives_pension_credit) calculates "
        "that family's Pension Credit in a branch with every housing costs "
        "element set to nil, and in that branch this variable reads the "
        "award without housing costs. The branch decides only that "
        "exemption. A member of the non-dependant family gains or loses it "
        "through this variable only where the family gets Pension Credit "
        "with the severe disability addition and none without it, and the "
        "member has no other exemption: someone who receives armed forces "
        "independence payment and no other qualifying benefit, or a blind "
        "partner under SPC Sch I para 1(1)(c) who receives none. There the "
        "model can exempt a non-dependant whom the law does not, or the "
        "reverse. Where an input or a scenario stores universal_credit for "
        "the period, or a reform neutralizes it, reading it cannot cycle, so "
        "this reads the award itself (receives_uc_carer_element). The model "
        "applies the same rule in Northern Ireland, whose legislation uses "
        "the same words: Welfare Reform (Northern Ireland) Order 2015 art. "
        "10, UC Regs (NI) 2016 regs 17 and 30, SPC Regs (NI) 2003 Sch 1 para "
        "1 as SR 2016/236 reg 31(7) amended it, and HB Regs (NI) 2006 Sch 4 "
        "para 14(2)(a)(iii)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/29",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/17",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/16",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/nisi/2015/2006/article/10",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/17",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/30",
        "https://www.legislation.gov.uk/nisr/2016/216/schedule/4/paragraph/15",
        "https://www.legislation.gov.uk/nisr/2003/28/schedule/1/paragraph/1",
        "https://www.legislation.gov.uk/nisr/2016/236/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4/paragraph/14",
    )

    def formula(person, period, parameters):
        if award_reads_no_other_variable(person.simulation, period):
            return person("receives_uc_carer_element", period)
        benunit = person.benunit
        # The award before the cap: DWP exempts a carer-element award from
        # the cap, and universal_credit's cap reads Pension Credit.
        award = benunit("universal_credit_pre_benefit_cap", period)
        includes_carer_element = benunit("uc_carer_element", period) > 0
        included = person("uc_carer_element_included_for_claimant", period)
        return included & includes_carer_element & (award > 0)
