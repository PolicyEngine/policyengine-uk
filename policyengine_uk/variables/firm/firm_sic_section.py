from policyengine_uk.model_api import *


class SICSection(Enum):
    UNKNOWN = "Unknown"
    A = "Agriculture, forestry and fishing"
    B = "Mining and quarrying"
    C = "Manufacturing"
    D = "Electricity, gas, steam and air conditioning supply"
    E = "Water supply; sewerage, waste management and remediation activities"
    F = "Construction"
    G = "Wholesale and retail trade; repair of motor vehicles and motorcycles"
    H = "Transportation and storage"
    I = "Accommodation and food service activities"
    J = "Information and communication"
    K = "Financial and insurance activities"
    L = "Real estate activities"
    M = "Professional, scientific and technical activities"
    N = "Administrative and support service activities"
    O = "Public administration and defence; compulsory social security"
    P = "Education"
    Q = "Human health and social work activities"
    R = "Arts, entertainment and recreation"
    S = "Other service activities"
    T = "Activities of households as employers"
    U = "Activities of extraterritorial organisations and bodies"


class firm_sic_section(Variable):
    value_type = Enum
    entity = Firm
    label = "Firm industry (SIC section)"
    documentation = "Section of the UK Standard Industrial Classification of economic activities 2007 (SIC 2007) of the firm's main activity."
    definition_period = YEAR
    possible_values = SICSection
    default_value = SICSection.UNKNOWN
