from policyengine_uk.data import EnhancedFRS
from policyengine_uk import Microsimulation
from policyengine_core.testing import generate_tests


test_parameter = generate_tests(
    Microsimulation(dataset=EnhancedFRS, year=2022)
)
