# PolicyEngine UK

[![PyPI version](https://badge.fury.io/py/policyengine-uk.svg)](https://badge.fury.io/py/policyengine-uk)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

PolicyEngine UK is [PolicyEngine](https://policyengine.org)'s microsimulation model of the UK tax-benefit system.
It uses the PolicyEngine Core microsimulation framework, which is based on [OpenFisca](https://openfisca.org).

The elements are described in different folders. All the modelling happens within the `policyengine_uk` folder.

- The rates and other system parameters are in the `parameters` folder.
- The formulas and inputs are in the `variables` folder.
- This country package comes also with reforms in the `reforms` folder.

The files that are outside from the `policyengine_uk` folder are used to set up the development environment. Installation instructions are located along with other documentation in the `docs` folder.

The model supports multiple different input datasets provided by the user, one of which is the Family Resources Survey,[^1] containing microdata on household incomes across the UK.
PolicyEngine UK enhances this dataset by fusing it to other surveys and reweighting it to minimize a comprehensive loss metric that measures the difference from an array of administrative totals.

[^1]: Department for Work and Pensions, Office for National Statistics, NatCen Social Research. (2021). Family Resources Survey, 2019-2020. [data collection]. UK Data Service. SN: 8802, http://doi.org/10.5255/UKDA-SN-8802-1


## Fast setup instructions

1. Run `pip install policyengine-uk`

2. Run `policyengine-uk` and go through the prompt to setup microdata.


## Contact

The primary maintainer for PolicyEngine UK is Nikhil Woodruff, co-founder and CTO of PolicyEngine (nikhil@policyengine.org).


## Citation

You may cite the source of your analysis as "PolicyEngine UK release #.#.#, author's calculations."
