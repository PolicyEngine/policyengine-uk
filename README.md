# OpenFisca UK

This extension of [OpenFisca](https://github.com/openfisca/country-template) aims to model the UK Tax-Benefit system.

This is in the early stages (from the country template linked above) and documentation and better modeling is in progress - feel free to contact or open an issue with bugs/errors/inaccuracies/suggestions.

The elements are described in different folders. All the modelling happens within the `openfisca_uk` folder.

- The rates and other system parameters are in the `parameters` folder.
- The formulas and inputs are in the `variables` folder.
- This country package comes also with reforms in the `reforms` folder.

The files that are outside from the `openfisca_uk` folder are used to set up the development environment. Installation instructions are located along with other documentation in the ```docs``` folder.

## Contact

The maintainer for OpenFisca-UK is Nikhil Woodruff - feel free to contact via [email](mailto:nikhil.woodruff@ubicenter.org).

## Disclaimer

The model is currently under development. Users should be forewarned that the
model components could change significantly. Therefore, there is NO GUARANTEE
OF ACCURACY. THE CODE SHOULD NOT CURRENTLY BE USED FOR PUBLICATIONS, JOURNAL
ARTICLES, OR RESEARCH PURPOSES. Essentially, you should assume the calculations are unreliable until we finish the code re-architecture and have checked the results against other existing implementations of the tax code. The package will have released versions, which will be checked against existing code prior to release.

## Citation

You may cite the source of your analysis as "OpenFisca-UK release #.#.#, author's calculations."
