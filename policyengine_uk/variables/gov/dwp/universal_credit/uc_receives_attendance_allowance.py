from policyengine_uk.model_api import *


class uc_receives_attendance_allowance(Variable):
    value_type = bool
    entity = Person
    label = "In receipt of attendance allowance for Universal Credit"
    documentation = (
        "Whether the person receives attendance allowance as the Secretary of "
        "State defines it in regulation 2 of the Universal Credit Regulations "
        "2013. The definition lists five heads: (a) attendance allowance under "
        "section 64 of the Social Security Contributions and Benefits Act "
        "1992; (b) an increase of disablement pension under section 104 or 105 "
        "of that Act, where constant attendance is needed or for exceptionally "
        "severe disablement; (d) a payment under article 14, 15, 16, 43 or 44 "
        "of the Personal Injuries (Civilians) Scheme 1983, or any analogous "
        "payment; (e) any payment for the need for attendance added to a war "
        "disablement pension; and (f) armed forces independence payment. The "
        "Secretary of State omitted head (c) in 2013 (S.I. 2013/1508). The "
        "model counts heads (a) and (f), from "
        "gov.dwp.universal_credit.attendance_allowance_benefits. It holds no "
        "separate amount for the other three, so it does not count a person "
        "who receives only one of them: iidb holds one reported amount with no "
        "constant attendance or exceptionally severe disablement increase of "
        "its own, afcs holds war disablement pensions without any attendance "
        "addition, and no variable holds Personal Injuries (Civilians) Scheme "
        "payments."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/2",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit
        return add(person, period, p.attendance_allowance_benefits) > 0
