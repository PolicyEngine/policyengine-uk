from policyengine_uk.model_api import *


class cares_for_severely_disabled_person(Variable):
    value_type = bool
    entity = Person
    label = "Cares for a severely disabled person"
    documentation = (
        "Whether the person this person cares for, in the household or "
        "outside it, gets a benefit that makes them a severely disabled "
        "person for Carer's Allowance (SSCBA 1992 s.70(2), with the payments "
        "that SI 1976/409 reg 3 prescribes) or a qualifying disability "
        "benefit for Carer Support Payment (SSI 2023/302 regs 2 and 5(1)). "
        "The Department for Work and Pensions pays Carer's Allowance only for "
        "caring for a severely disabled person (s.70(1)), Social Security "
        "Scotland pays Carer Support Payment only for care of a person to "
        "whom a qualifying disability benefit is normally payable (reg 5(1)), "
        "and the Universal Credit carer element needs the Carer's Allowance "
        "conditions, apart from the earnings limit and residence in Scotland "
        "(UC Regs 2013 reg 30(1)(a)). Caring hours in the survey count care "
        "for anyone and don't say whom the carer cares for, and the person "
        "cared for can live elsewhere, so the model doesn't derive this from "
        "the household's disability benefits: it takes the person cared for "
        "to qualify unless an input says otherwise, and the default is true. "
        "The model reads it only on the route through caring hours "
        "(care_hours at the minimum) to Carer's Allowance, Carer Support "
        "Payment and is_carer_for_benefits, and so the Universal Credit "
        "carer element, and in the hours that explain an entitlement in "
        "partners_care_for_same_severely_disabled_person. A reported award "
        "(carers_allowance_reported, the model's reported-receipt input for "
        "both benefits) still counts whatever this input says, since the "
        "Department or Social Security Scotland pays it. Set it to false for "
        "a carer whose caring hours go to someone with none of those "
        "benefits."
    )
    definition_period = YEAR
    default_value = True
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s. 70(1) and (2)",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        ),
        dict(
            title="The Social Security (Invalid Care Allowance) Regulations 1976 reg. 3",
            href="https://www.legislation.gov.uk/uksi/1976/409/regulation/3",
        ),
        dict(
            title="The Carer's Assistance (Carer Support Payment) (Scotland) Regulations 2023 reg. 2(2)",
            href="https://www.legislation.gov.uk/ssi/2023/302/regulation/2",
        ),
        dict(
            title="The Carer's Assistance (Carer Support Payment) (Scotland) Regulations 2023 reg. 5(1)",
            href="https://www.legislation.gov.uk/ssi/2023/302/regulation/5",
        ),
        dict(
            title="The Universal Credit Regulations 2013 reg. 30(1)(a)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/30",
        ),
    ]
