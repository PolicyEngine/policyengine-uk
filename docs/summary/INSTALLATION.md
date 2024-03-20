## Install Instructions for Users and Contributors

This package requires [Python 3.7](https://www.python.org/downloads/release/python-370/). More recent versions should work, but are not tested.

All platforms that can execute Python are supported, which includes GNU/Linux, macOS and Microsoft Windows (in which case we recommend using [ConEmu](https://conemu.github.io/) instead of the default console).

### Setting-up a Virtual Environment with Pew

In order to limit dependencies conflicts, we recommend to use a [virtual environment](https://virtualenv.pypa.io/en/stable/) (abbreviated as “virtualenv”) with a virtualenv manager such as [pew](https://github.com/berdario/pew).

- A [virtualenv](https://virtualenv.pypa.io/en/stable/) is a project specific environment created to suit the needs of the project you are working on.
- A virtualenv manager such as [pew](https://github.com/berdario/pew) lets you easily create, remove and toggle between several virtualenvs.

To install pew, launch a terminal on your computer and follow these instructions:

```sh
pip install --upgrade pip
pip install pew  # if asked, answer "Y" to the question about modifying your shell config file.
pew new policyengine --python=python3.7  # create a new virtualenv called “policyengine”
```

The virtualenv you just created will be automatically activated. This means you will operate in the virtualenv immediately. You should see a prompt resembling this:

```
Installing setuptools, pip, wheel...done.
Launching subshell in virtual environment. Type 'exit' or 'Ctrl+D' to return.
```

You can re-activate that virtualenv at any time with `pew workon policyengine`.

:tada: You are now ready to install this PolicyEngine Country Package!

Two install procedures are available. Pick procedure A or B below depending on how you plan to use this Country Package.

### A. Minimal Installation (Pip Install)

Follow this installation if you wish to:

- run calculations on a large population;
- create tax & benefits simulations;
- write an extension to this legislation (e.g. city specific tax & benefits);

For more advanced uses, head to the [Advanced Installation](#advanced-installation-git-clone).

#### Install this Country Package with Pip Install

Inside your virtualenv, check the prerequisites:

```sh
python --version  # should print "Python 2.7.xx".
#if not, make sure you pass the python version as an argument when creating your virtualenv
```

```sh
pip --version  # should print at least 9.0.
#if not, run "pip install --upgrade pip"
```

Install the Country Package:

```sh
pip install policyengine_uk
```

:tada: This OpenFPolicyEngineisca Country Package is now installed and ready!


### B. Advanced Installation (Git Clone)

Follow this tutorial if you wish to:

- create or change this Country Package's legislation;
- contribute to the source code.

#### Clone this Country Package with Git

First of all, make sure [Git](https://www.git-scm.com/) is installed on your machine.

Set your working directory to the location where you want this PolicyEngine Country Package cloned.

Inside your virtualenv, check the prerequisites:

```sh
python --version  # should print "Python 2.7.xx".
#if not, make sure you pass the python version as an argument when creating your virtualenv
```

```sh
pip --version  # should print at least 9.0.
#if not, run "pip install --upgrade pip"
```

Clone this Country Package on your machine:

```sh
git clone https://github.com/policyengine/policyengine-uk.git
cd policyengine-uk
pip install --editable .[dev]
```

You can make sure that everything is working by running the provided tests with `make test`.

:tada: This PolicyEngine Country Package is now installed and ready!
