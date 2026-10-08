from datetime import date

from policyengine_uk.model_api import *


class housing_benefit_assessment_date(Variable):
    value_type = date
    entity = BenUnit
    definition_period = YEAR
    label = "Housing Benefit date for factual status and retained capital"
    documentation = "Point-in-time assessment date for supplied status, duration and retained-capital facts. Defaults to 6 October, consistently with UK annual age inputs. This is a stock/status convention, not a prediction that policy remains unchanged. Annual awards hold these facts fixed unless a formula explicitly segments a policy change. Supply a different assessment date when known."

    def formula(benunit, period, parameters):
        return np.full(
            benunit.nb_persons().shape,
            f"{period.start.year}-10-06",
            dtype="datetime64[D]",
        )
