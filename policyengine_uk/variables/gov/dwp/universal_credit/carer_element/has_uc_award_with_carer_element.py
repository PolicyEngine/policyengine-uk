from policyengine_uk.model_api import *


class has_uc_award_with_carer_element(Variable):
    value_type = bool
    entity = Person
    label = "has a Universal Credit award with the carer element, read before the award"
    documentation = (
        "Whether this person has an award of Universal Credit which includes "
        "the carer element (Universal Credit Regulations 2013 reg 29) in "
        "respect of them, read from the conditions of the award rather than "
        "its amount: the family claims Universal Credit "
        "(claims_universal_credit), meets the age, pension-route and capital "
        "conditions (is_uc_eligible), and the award includes the carer "
        "element in respect of this claimant "
        "(uc_carer_element_included_for_claimant). It is the carer condition "
        "of the legacy severe disability premium (HB Regs 2006 Sch 3 para "
        "14(2)(a)(iii) and (b)) and of the Pension Credit severe disability "
        "addition (SPC Regs 2002 Sch I para 1(1) and (4)), through "
        "is_cared_for_by_carer_benefit_recipient. Those cannot read the award "
        "itself: the housing costs element's non-dependant deduction reads "
        "Pension Credit, which reads the addition. A claimant whose income "
        "tapers the award to nil fails the financial conditions (Welfare "
        "Reform Act 2012 s.5(1)(b) and (2)(b); the minimum is one penny, reg "
        "17), so has no award in law, but still counts here. So does a family "
        "that forgoes Universal Credit for Tax-Free Childcare "
        "(forgoes_universal_credit_for_tax_free_childcare reads the award). "
        "receives_uc_carer_element is the same test on a positive award, for "
        "readers that can read it."
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
        benunit = person.benunit
        on_claim = benunit("claims_universal_credit", period) & benunit(
            "is_uc_eligible", period
        )
        included = person("uc_carer_element_included_for_claimant", period)
        return on_claim & included
