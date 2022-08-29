# OpenFisca UK

OpenFisca UK is [PolicyEngine](https://policyengine.org)'s microsimulation model of the UK tax-benefit system, applying the [OpenFisca](https://openfisca.org) microsimulation framework.

The elements are described in different folders. All the modelling happens within the `openfisca_uk` folder.

- The rates and other system parameters are in the `parameters` folder.
- The formulas and inputs are in the `variables` folder.
- This country package comes also with reforms in the `reforms` folder.

The files that are outside from the `openfisca_uk` folder are used to set up the development environment. Installation instructions are located along with other documentation in the `docs` folder.

The model supports multiple different input datasets provided by the user, one of which is the Family Resources Survey,[^1] containing microdata on household incomes across the UK. OpenFisca UK enhances this dataset by fusing it to other surveys and reweighting it to minimize a comprehensive loss metric that measures the difference from an array of administrative totals.

[^1]: Department for Work and Pensions, Office for National Statistics, NatCen Social Research. (2021). Family Resources Survey, 2019-2020. [data collection]. UK Data Service. SN: 8802, http://doi.org/10.5255/UKDA-SN-8802-1


## Fast setup instructions

1. Run `pip install openfisca-uk`

2. Run `openfisca-uk` and go through the prompt to setup microdata.


## Contact

The primary maintainer for OpenFisca-UK is Nikhil Woodruff, co-founder and CTO of PolicyEngine (nikhil@policyengine.org).


## Citation

You may cite the source of your analysis as "OpenFisca-UK release #.#.#, author's calculations."
