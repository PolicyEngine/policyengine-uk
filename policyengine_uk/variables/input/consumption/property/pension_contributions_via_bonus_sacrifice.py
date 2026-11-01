from policyengine_uk.model_api import *


class pension_contributions_via_bonus_sacrifice(Variable):
    label = "Pension contributions via bonus sacrifice"
    documentation = (
        "Annual employer pension contributions made in place of a bonus the "
        "employee gives up. The tax and NICs rules treat bonus sacrifice as "
        "salary sacrifice, and the NICs exemption cap covers the two together, "
        "so every formula reads this input summed with "
        "pension_contributions_via_salary_sacrifice. It is a separate input "
        "because sources measure the two routes apart: ASHE, the source of "
        "HMRC's salary sacrifice estimates, does not cover bonus sacrifice, and "
        "the OBR costs the bonus route on its own tax base. Cash pay "
        "(employment_income) is net of the sacrificed bonus."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        dict(
            title="OBR, Costing of charging NICs on salary-sacrificed pension contributions (February 2026), paragraphs 1.4, 1.5 and 1.9",
            href="https://obr.uk/docs/dlm_uploads/Supplementary-forecast-information-salary-sacrifice-costing-1.pdf",
        ),
        dict(
            title="Finance Act 2004 s. 228ZA(6): relevant flexible remuneration arrangements",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/228ZA",
        ),
    ]
    uprating = "gov.economic_assumptions.indices.obr.average_earnings"
