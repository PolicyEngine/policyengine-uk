from policyengine_uk.model_api import *


class firm_zero_rated_class_1_earnings(Variable):
    value_type = float
    entity = Firm
    label = "Firm Class 1 earnings in a zero-rate band"
    documentation = (
        "Earnings of the firm's employees between the secondary threshold and "
        "the upper threshold of a 0% secondary band: the upper secondary "
        "threshold for an earner under 21 (SSCBA 1992 s.9A), the apprentice "
        "upper secondary threshold for a relevant apprentice under 25 (s.9B), "
        "or the freeport or investment zone upper secondary threshold for an "
        "eligible employee (National Insurance Contributions Act 2022 s.1). "
        "The caller applies the relevant threshold to each employee; the "
        "firm-level model has no per-employee pay."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.9A",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/9A",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.9B",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/9B",
        ),
        dict(
            title="National Insurance Contributions Act 2022 s.1",
            href="https://www.legislation.gov.uk/ukpga/2022/9/section/1",
        ),
    ]
