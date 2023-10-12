# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="PolicyEngine-UK",
    version="0.56.3",
    author="PolicyEngine",
    author_email="nikhil@policyengine.org",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    description="PolicyEngine tax and benefit system for the UK",
    keywords="benefit microsimulation social tax",
    license="http://www.fsf.org/licensing/licenses/agpl-3.0.html",
    url="https://github.com/PolicyEngine/policyengine-uk",
    include_package_data=True,  # Will read MANIFEST.in
    data_files=[
        (
            "share/openfisca/openfisca-country-template",
            ["CHANGELOG.md", "LICENSE", "README.md"],
        ),
    ],
    install_requires=[
        "argparse>=1.4.0",
        "click>=8.0.0",
        "gif[plotly]>=3.0.0",
        "inquirer>=2.7.0",
        "microdf_python>=0.3.0",
        "pandas",
        "plotly>=4.14.3",
        "PolicyEngine-Core>=2.8.1,<3",
        "pyyaml>=5.3.1",
        "pytest",
        "requests>=2.25.1",
        "synthimpute",
        "tqdm>=4.59.0",
        "yaml-changelog>=0.1.5",
    ],
    extras_require={
        "dev": [
            "black",
            "coverage",
            "furo<2023",
            "jupyter-book",
            "linecheck",
            "markupsafe==2.0.1",
            "plotly",
            "pydata-sphinx-theme==0.13.1",
            "pytest",
            "setuptools",
            "sphinx>=4.5.0,<5",
            "sphinx-argparse>=0.3.2,<1",
            "sphinx-math-dollar>=1.2.1,<2",
            "survey-enhance",
            "wheel",
            "yaml-changelog>=0.1.7",
        ]
    },
    # Windows CI requires Python 3.9.
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [],
    },
    packages=find_packages(),
)
