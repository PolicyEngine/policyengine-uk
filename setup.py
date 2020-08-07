# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = "OpenFisca-Country-Template",
    version = "3.9.10",
    author = "OpenFisca Team",
    author_email = "contact@openfisca.org",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: Information Analysis",
        ],
    description = "OpenFisca tax and benefit system for Country-Template",
    keywords = "benefit microsimulation social tax",
    license ="http://www.fsf.org/licensing/licenses/agpl-3.0.html",
    url = "https://github.com/openfisca/country-template",
    include_package_data = True,  # Will read MANIFEST.in
    data_files = [
        ("share/openfisca/openfisca-country-template", ["CHANGELOG.md", "LICENSE", "README.md"]),
        ],
    install_requires = [
        "OpenFisca-Core[web-api] >=27.0,<35.0",
        ],
    extras_require = {
        "dev": [
            "autopep8 ==1.5",
            "flake8 >=3.5.0,<3.8.0",
            "flake8-print",
            "pycodestyle >=2.3.0,<2.6.0",  # To avoid incompatibility with flake
            ]
        },
    packages=find_packages(),
    )
