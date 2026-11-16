from policyengine_uk.model_api import *


class company_car_registered_from_6_april_2020(Variable):
    value_type = bool
    entity = Person
    label = "Company car first registered on or after 6 April 2020"
    documentation = (
        "In 2020-21 and 2021-22 a car first registered on or after 6 April "
        "2020 has lower appropriate percentages (ITEPA 2003 s. 139A, "
        "inserted for each year by Finance Act 2020 ss. 9 and 10). From "
        "2022-23 every car takes the same rates and this has no effect."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Finance Act 2020 s. 9",
            href="https://www.legislation.gov.uk/ukpga/2020/14/section/9/enacted",
        ),
        dict(
            title="Finance Act 2020 s. 10",
            href="https://www.legislation.gov.uk/ukpga/2020/14/section/10/enacted",
        ),
    ]
