from openfisca_uk.system import CountryTaxBenefitSystem


class variable_holder(type):
    contents = {
        variable.name: type(variable)
        for variable in CountryTaxBenefitSystem().variables.values()
    }

    def __getattr__(cls, name):
        return cls.contents[name]


class variables(metaclass=variable_holder):
    pass
