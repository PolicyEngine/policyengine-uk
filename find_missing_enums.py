import os
import re
import ast


def find_undefined_names(directory):
    """Find all potentially undefined names in Python files."""
    undefined = set()

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r") as f:
                        content = f.read()

                    # Look for patterns like "possible_values = SomeName" or "SomeName.VALUE"
                    enum_refs = re.findall(
                        r"possible_values\s*=\s*(\w+)", content
                    )
                    enum_refs.extend(
                        re.findall(
                            r"(\w+)\.(?:NONE|LOWER|HIGHER|MIDDLE|STANDARD|ENHANCED|MALE|FEMALE|SINGLE|COUPLE)",
                            content,
                        )
                    )

                    for name in enum_refs:
                        if name not in [
                            "self",
                            "person",
                            "household",
                            "benunit",
                            "parameters",
                        ]:
                            # Check if it's defined in the file
                            if f"class {name}" not in content:
                                undefined.add((name, filepath))

                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

    return undefined


undefined_names = find_undefined_names("policyengine_uk/variables/")
for name, filepath in sorted(undefined_names):
    print(f"{name} used in {filepath}")
