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
        "Those cannot read the award: its non-dependant deduction spares a "
        "non-dependant on Pension Credit, so it reads Pension Credit, which "
        "reads the addition. So this reads the award's conditions instead. "
        "The family claims Universal Credit (claims_universal_credit), meets "
        "the age, pension-route and capital conditions (is_uc_eligible) and "
        "has an award before the non-dependant deduction (uc_award_upper_bound "
        "positive), and the award includes the carer element in respect of "
        "this claimant (uc_carer_element_included_for_claimant). Where the "
        "bound is nil, the award is nil and there is no award (Welfare Reform "
        "Act 2012 s.5(1)(b) and (2)(b); the minimum is one penny, reg 17), so "
        "a carer whose income tapers the award to nil does not count. A carer "
        "whose award a non-dependant deduction takes to nil still counts, and "
        "so does a family that takes Tax-Free Childcare instead "
        "(forgoes_universal_credit_for_tax_free_childcare reads the award). "
        "Where an input or a scenario stores universal_credit for the period, "
        "or a reform neutralizes it, reading it cannot cycle, so this reads "
        "the award itself (receives_uc_carer_element)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/29",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/17",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
    )

    def formula(person, period, parameters):
        if award_reads_no_other_variable(person.simulation, period):
            return person("receives_uc_carer_element", period)
        benunit = person.benunit
        on_claim = (
            benunit("claims_universal_credit", period)
            & benunit("is_uc_eligible", period)
            & (benunit("uc_award_upper_bound", period) > 0)
        )
        included = person("uc_carer_element_included_for_claimant", period)
        return on_claim & included
