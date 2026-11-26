from policyengine_uk.model_api import *


class has_qualifying_site_or_mooring_liability(Variable):
    value_type = bool
    entity = BenUnit
    label = "Liable for qualifying site or mooring payments"
    documentation = (
        "Whether this family has an actual or prescribed deemed liability "
        "for qualifying mooring charges for a houseboat, or site payments "
        "for a caravan or mobile home, occupied as its home. Supply this "
        "payment-type and liability fact after establishing that the payment "
        "qualifies under the housing-payment rules outside the model. "
        "It does not establish "
        "overall benefit eligibility: programme-specific age, claim and "
        "accommodation conditions still apply. Enter the qualifying amount "
        "in benunit_rent; benunit_is_rent_liable remains a separate liability "
        "condition. This input covers site and mooring payments only, not "
        "ordinary mortgage payments or other owner costs. It does not "
        "determine tenancy, rent allocation or the household head's liability."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/12",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/12",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/13",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/13",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/1/paragraph/2",
        "https://www.legislation.gov.uk/nisr/2016/216/schedule/1/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/25",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/26",
    )
