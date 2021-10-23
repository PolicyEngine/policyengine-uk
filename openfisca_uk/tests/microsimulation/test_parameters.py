from openfisca_uk_data import FRS
from openfisca_uk import Microsimulation
from openfisca_tools.testing import generate_tests


test_parameter = generate_tests(Microsimulation(dataset=FRS, year=2019))
