Thank you for wanting to contribute to PolicyEngine! :smiley:

TL;DR: [GitHub Flow](https://guides.github.com/introduction/flow/), [SemVer](http://semver.org/).

## Pull requests

We follow the [GitHub Flow](https://guides.github.com/introduction/flow/): all code contributions are submitted via a pull request towards the `master` branch.

Opening a Pull Request means you want that code to be merged. If you want to only discuss it, send a link to your branch along with your questions through whichever communication channel you prefer.

Please make sure (if you're changing the package; you don't have to for documentation or package health changes) to add to changelog_entry.yaml and run 'make changelog', then commit the results.

### Peer reviews

All pull requests must be reviewed by someone else than their original author.

> In case of a lack of available reviewers, one may review oneself, but only after at least 24 hours have passed without working on the code to review.

To help reviewers, make sure to add to your PR a **clear text explanation** of your changes.

In case of breaking changes, you **must** give details about what features were deprecated.

> You must also provide guidelines to help users adapt their code to be compatible with the new version of the package.

## Advertising changes

### Version number

We follow the [semantic versioning](http://semver.org/) spec: any change impacts the version number, and the version number conveys API compatibility information **only**.

Examples:

#### Patch bump

- Fixing or improving an already existing calculation.

#### Minor bump

- Adding a variable to the tax and benefit system.

#### Major bump

- Renaming or removing a variable from the tax and benefit system.

