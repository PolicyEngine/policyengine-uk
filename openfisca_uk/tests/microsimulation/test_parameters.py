from openfisca_uk.data import EnhancedFRS
from openfisca_uk import Microsimulation
from openfisca_tools.testing import generate_tests


test_parameter = generate_tests(
    Microsimulation(dataset=EnhancedFRS, year=2022)
)
