# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="OpenFisca-UK",
    version="0.7.9",
    author="PolicyEngine",
    author_email="nikhil@policyengine.org",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    description="OpenFisca tax and benefit system for UK",
    keywords="benefit microsimulation social tax",
    license="http://www.fsf.org/licensing/licenses/agpl-3.0.html",
    url="https://github.com/pslmodels/openfisca-uk",
    include_package_data=True,  # Will read MANIFEST.in
    data_files=[
        (
            "share/openfisca/openfisca-country-template",
            ["CHANGELOG.md", "LICENSE", "README.md"],
        ),
    ],
    install_requires=[
        "requests>=2.25.1",
        "pandas>=1.1.4",
        "numpy>=1.17.5",
        "pyyaml>=5.3.1",
        "pytest>=5.4.3",
        "OpenFisca-Core>=35.4.1",
        "microdf_python>=0.3.0",
        "OpenFisca-UK-Data>=0.5.0",
        "OpenFisca-Tools>=0.1.7,<0.2.0",
        "tqdm>=4.59.0",
        "plotly>=4.14.3",
        "argparse>=1.4.0",
        "inquirer>=2.7.0",
    ],
    extras_require={
        "dev": [
            "autopep8 >=1.5",
            "flake8 >=3.5.0,<3.8.0",
            "flake8-print",
            "pycodestyle >=2.3.0,<2.6.0",  # To avoid incompatibility with flake
        ]
    },
    entry_points={
        "console_scripts": [
            "openfisca-uk-setup=openfisca_uk.initial_setup:main"
        ],
    },
    packages=find_packages(),
)
