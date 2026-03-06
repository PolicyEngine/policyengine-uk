from policyengine_core.model_api import Parameter

from policyengine_uk.system import system

parameters = list(
    filter(
        lambda x: isinstance(x, Parameter),
        system.parameters.gov.get_descendants(),
    )
)

"""
Remove for now.
@pytest.mark.parametrize("parameter", parameters, ids=lambda x: x.name)
def test_parameter_has_label(parameter):
    assert parameter.metadata.get("label") is not None, "Missing label"

"""
