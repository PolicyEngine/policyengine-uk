from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


class pip_dl(Variable):
    label = "PIP (daily living)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/387/regulation/5",
        "https://www.legislation.gov.uk/nisr/2016/227/regulation/5",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.pip
        pip_dl = p.daily_living
        category = person("pip_dl_category", period)
        # No claim may be made below the minimum age (SI 2013/387 reg 5(1);
        # NI SR 2016/227 reg 5(1)), so no award is paid below it.
        old_enough = person("age", period) >= p.min_age
        award = (
            select(
                [
                    category == PIPCategory.ENHANCED,
                    category == PIPCategory.STANDARD,
                    category == PIPCategory.NONE,
                ],
                [
                    pip_dl.enhanced,
                    pip_dl.standard,
                    0,
                ],
            )
            * WEEKS_IN_YEAR
        )
        return where(old_enough, award, 0)
