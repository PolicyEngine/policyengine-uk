# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="PolicyEngine-UK",
    version="0.41.11",
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
        "pandas",
        "numpy>=1.17.5",
        "pyyaml>=5.3.1",
        "pytest>=5.4.3",
        "PolicyEngine-Core>=1.11.1,<2",
        "microdf_python>=0.3.0",
        "tqdm>=4.59.0",
        "plotly>=4.14.3",
        "argparse>=1.4.0",
        "inquirer>=2.7.0",
        "gif[plotly]>=3.0.0",
        "yaml-changelog>=0.1.5",
        "click>=8.0.0",
        "synthimpute",
        "google-cloud-storage",
    ],
    extras_require={
        "dev": [
            "black",
            "coverage",
            "jupyter-book",
            "plotly",
            "pytest",
            "setuptools",
            "wheel",
            "yaml-changelog>=0.1.7",
            "linecheck",
            "furo<2023",
            "markupsafe==2.0.1",
            "sphinx>=4.5.0,<5",
            "sphinx-argparse>=0.3.2,<1",
            "sphinx-math-dollar>=1.2.1,<2",
        ]
    },
    entry_points={
        "console_scripts": [],
    },
    packages=find_packages(),
)
