# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="PolicyEngine-UK",
    version="2.33.0",
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
        "PolicyEngine-Core>=3.6.4",
        "microdf_python",
    ],
    extras_require={
        "dev": [
            "tqdm",
            "black",
            "coverage",
            "furo<2023",
            "jupyter-book",
            "linecheck",
            "pytest",
            "setuptools",
            "sphinx-argparse>=0.3.2,<1",
            "sphinx-math-dollar>=1.2.1,<2",
            "wheel",
            "yaml-changelog>=0.1.7",
            "snowballstemmer>=2,<3",
        ]
    },
    # Windows CI requires Python 3.9.
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [],
    },
    packages=find_packages(),
)
