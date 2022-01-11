from openfisca_uk.model_api import *

class wtc_worker_element(Variable):
    label = "WTC worker element"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2005/part/2/crossheading/30-hour-element"

    def formula(benunit, period, parameters):
        wtc = parameters(period).hmrc.tax_credits.working_tax_credit
        person = benunit.members
        hours = person("weekly_hours", period)
        is_joint = benunit("is_joint_benunit", period)
        has_children = benunit("benunit_has_children_or_qyp", period)
        lower_hours = hours >= wtc.eligibility.work_requirements.lower
        worker_hours = hours >= wtc.elements.worker.hours
        meets_standard_condition = benunit.any(worker_hours)
        meets_reduced_condition = (
            is_joint
            & has_children
            & (benunit.sum(hours) >= wtc.elements.worker.hours)
            & benunit.any(lower_hours)
        )
        amount = wtc.elements.worker.rate
        return amount * (meets_standard_condition | meets_reduced_condition)