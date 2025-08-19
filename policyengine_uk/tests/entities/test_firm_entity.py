import pytest
from policyengine_uk import CountryTaxBenefitSystem


def test_firm_entity_exists():
    """Test that the Firm entity is defined in the tax-benefit system."""
    system = CountryTaxBenefitSystem()

    # Find Firm entity in the list
    firm_entity = None
    for entity in system.entities:
        if entity.key == "firm":
            firm_entity = entity
            break

    assert firm_entity is not None, "Firm entity not found"
    assert firm_entity.key == "firm"
    assert firm_entity.plural == "firms"
    assert firm_entity.label == "Firm"


def test_firm_entity_has_owner_role():
    """Test that the Firm entity has an owner role linking to Person."""
    system = CountryTaxBenefitSystem()

    # Find Firm entity
    firm_entity = None
    for entity in system.entities:
        if entity.key == "firm":
            firm_entity = entity
            break

    assert firm_entity is not None, "Firm entity not found"

    # Check that the entity has roles
    assert len(firm_entity.roles) > 0

    # Find the owner role
    owner_role = None
    for role in firm_entity.roles:
        if role.key == "owner":
            owner_role = role
            break

    assert owner_role is not None
    assert owner_role.plural == "owners"
    assert owner_role.label == "Owner"


def test_firm_entity_documentation():
    """Test that the Firm entity has proper documentation."""
    system = CountryTaxBenefitSystem()

    # Find Firm entity
    firm_entity = None
    for entity in system.entities:
        if entity.key == "firm":
            firm_entity = entity
            break

    assert firm_entity is not None, "Firm entity not found"
    assert firm_entity.doc is not None
    assert (
        "business" in firm_entity.doc.lower()
        or "firm" in firm_entity.doc.lower()
    )
