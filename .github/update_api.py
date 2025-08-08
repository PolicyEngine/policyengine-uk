import argparse
import tomllib
import os


def main():
    # First, find the current package version number from the setup.py file
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
        version = data["project"]["version"]
    # Then, clone the https://github.com/policyengine/policyengine-api repo using the GitHub CLI
    pat = os.environ["GITHUB_TOKEN"]
    os.system(
        f"git clone https://nikhilwoodruff:{pat}@github.com/policyengine/policyengine-api"
    )
    # Then, cd inside and run gcp/bump_country_package.py --country policyengine-uk --version {version}
    os.system(
        f"cd policyengine-api && python gcp/bump_country_package.py --country policyengine-uk --version {version}"
    )
    # Repeat the above for https://github.com/policyengine/policyengine-household-api
    os.system(
        f"git clone https://nikhilwoodruff:{pat}@github.com/policyengine/policyengine-household-api"
    )

    # Then, cd inside and run gcp/bump_country_package.py --country policyengine-uk --version {version}
    os.system(
        f"cd policyengine-household-api && python gcp/bump_country_package.py --country policyengine-uk --version {version}"
    )


if __name__ == "__main__":
    main()
