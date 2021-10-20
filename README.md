# OpenFisca UK

This extension of [OpenFisca](https://github.com/openfisca/country-template) aims to model the UK Tax-Benefit system.

This is in the early stages (from the country template linked above) and documentation and better modeling is in progress - feel free to contact or open an issue with bugs/errors/inaccuracies/suggestions.

The elements are described in different folders. All the modelling happens within the `openfisca_uk` folder.

- The rates and other system parameters are in the `parameters` folder.
- The formulas and inputs are in the `variables` folder.
- This country package comes also with reforms in the `reforms` folder.

The files that are outside from the `openfisca_uk` folder are used to set up the development environment. Installation instructions are located along with other documentation in the ```docs``` folder.

We're grateful to the [UKMOD](https://www.iser.essex.ac.uk/research/projects/ukmod) team for publishing descriptions of their model; our ability to reference these descriptions accelerated OpenFisca UK's development. UKMOD is maintained, developed and managed by the Centre for Microsimulation and Policy Analysis at the Institute for Social and Economic Research (ISER), University of Essex.

The model supports multiple different input datasets provided by the user, one of which is the Family Resources Survey[^1], containing microdata on household incomes across the UK.

[^1]: Department for Work and Pensions, Office for National Statistics, NatCen Social Research. (2021). Family Resources Survey, 2019-2020. [data collection]. UK Data Service. SN: 8802, http://doi.org/10.5255/UKDA-SN-8802-1

## Fast setup instructions

1. `pip install git+https://github.com/PSLmodels/openfisca-uk`

For microdata instructions, follow (from [openfisca-uk-data](https://github.com/nikhilwoodruff/openfisca-uk-data)):
2. Download the [synthetic FRS file](https://github.com/nikhilwoodruff/openfisca-uk-data/releases/download/synth-frs/synth_frs_2018.h5)
3. Run `openfisca-uk-data synth_frs save synth_frs_2018`

Or with the actual microdata:
2. Have the `8633~~~.zip` file ready
3. Run `openfisca-uk-data raw_frs generate 2018 8633~~~.zip`
4. Run `openfisca-uk-data frs generate 2018`

## Contact

The maintainer for OpenFisca-UK is Nikhil Woodruff - feel free to contact via [email](mailto:nikhil.woodruff@ubicenter.org).

## How is this model validated?

We constructed the model by programming rules and parameters specified primarily in the [country report](https://www.iser.essex.ac.uk/research/publications/working-papers/cempa/cempa7-20.pdf) created by [UKMOD](https://www.iser.essex.ac.uk/research/projects/ukmod), a microsimulation model developed by the University of Essex. We also validated against legislation, various gov.uk sites, reports from other microsimulation models, and external benefits calculators. See the [validation page](https://pslmodels.github.io/openfisca-uk/validation.html) for more information.

## Disclaimer

The model is currently under development. Users should be forewarned that the
model components could change significantly. Therefore, there is NO GUARANTEE
OF ACCURACY. THE CODE SHOULD NOT CURRENTLY BE USED FOR PUBLICATIONS, JOURNAL
ARTICLES, OR RESEARCH PURPOSES. Essentially, you should assume the calculations are unreliable until we finish the code re-architecture and have checked the results against other existing implementations of the tax code. The package will have released versions, which will be checked against existing code prior to release.

## Citation

You may cite the source of your analysis as "OpenFisca-UK release #.#.#, author's calculations."
