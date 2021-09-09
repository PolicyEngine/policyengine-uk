# OpenFisca UK

This extension of [OpenFisca](https://github.com/openfisca/country-template) aims to model the UK Tax-Benefit system.

This is in the early stages (from the country template linked above) and documentation and better modeling is in progress - feel free to contact or open an issue with bugs/errors/inaccuracies/suggestions.

The elements are described in different folders. All the modelling happens within the `openfisca_uk` folder.

- The rates and other system parameters are in the `parameters` folder.
- The formulas and inputs are in the `variables` folder.
- This country package comes also with reforms in the `reforms` folder.

The files that are outside from the `openfisca_uk` folder are used to set up the development environment. Installation instructions are located along with other documentation in the ```docs``` folder.

Policy implementations in OpenFisca-UK were accelerated by the descriptions provided by the UKMOD team. UKMOD is maintained, developed and managed by the Centre for Microsimulation and Policy Analysis at the Institute for Social and Economic Research (ISER), University of Essex. The process of extending and updating UKMOD is financially supported by the Nuffield Foundation (2018-2021). The results and their interpretation are the author’s(’) sole responsibility. See the [UKMOD website](https://www.iser.essex.ac.uk/research/projects/ukmod) for more details.

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

## Disclaimer

The model is currently under development. Users should be forewarned that the
model components could change significantly. Therefore, there is NO GUARANTEE
OF ACCURACY. THE CODE SHOULD NOT CURRENTLY BE USED FOR PUBLICATIONS, JOURNAL
ARTICLES, OR RESEARCH PURPOSES. Essentially, you should assume the calculations are unreliable until we finish the code re-architecture and have checked the results against other existing implementations of the tax code. The package will have released versions, which will be checked against existing code prior to release.

## Citation

You may cite the source of your analysis as "OpenFisca-UK release #.#.#, author's calculations."
