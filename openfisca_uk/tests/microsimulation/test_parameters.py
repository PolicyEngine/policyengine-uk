from openfisca_uk_data import FRSEnhanced
from openfisca_uk import Microsimulation
from openfisca_tools.testing import generate_tests


test_parameter = generate_tests(
    Microsimulation(dataset=FRSEnhanced, year=2019)
)
