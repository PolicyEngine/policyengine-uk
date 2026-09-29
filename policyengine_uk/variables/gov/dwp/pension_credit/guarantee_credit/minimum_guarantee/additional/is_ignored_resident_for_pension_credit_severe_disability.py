from policyengine_uk.model_api import *


class is_ignored_resident_for_pension_credit_severe_disability(Variable):
    value_type = bool
    entity = Person
    label = "Residence ignored for the Pension Credit severe disability addition"
    documentation = (
        "Whether this person's presence in the claimant's household is "
        "ignored for the Pension Credit severe disability addition for a "
        "reason the model does not otherwise observe. That covers someone "
        "who is: no longer certified blind but was within the last 28 weeks "
        "(SPC Regs 2002 Sch. I para. 2(2)(c)); a live-in carer engaged by a "
        "charitable or voluntary organisation that charges for the care, or "
        "that carer's partner (para. 2(2)(d)-(e)); a carer in their first 12 "
        "weeks in the household (para. 2(3)-(4)); a commercial lodger or "
        "landlord who is not a close relative, or a member of their household "
        "(para. 2(5)); a co-owner or joint tenant, or their partner (para. "
        "2(6)-(7), subject to para. 3(3)); or someone separately liable to the "
        "landlord for their own occupation, who does not reside with the "
        "claimant (para. 3(1)). Qualifying disability benefits, blindness "
        "certification and qualifying young person status are read from "
        "their own variables."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/3",
    )
