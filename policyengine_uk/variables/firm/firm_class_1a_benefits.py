from policyengine_uk.model_api import *


class firm_class_1a_benefits(Variable):
    value_type = float
    entity = Firm
    label = "Firm benefits in kind liable to Class 1A"
    documentation = (
        "Cash equivalent of the taxable benefits in kind the firm provides to "
        "its employees in the year, which are general earnings under ITEPA "
        "2003 but not Class 1 earnings, and on which the firm pays Class 1A "
        "contributions (SSCBA 1992 s.10(1))."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = 0
    unit = GBP
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s.10",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/10",
        ),
    ]
