#! /usr/bin/env bash

VERSION=$(python -c "import re; print(re.search(r'version = \"(.+?)\"', open('pyproject.toml').read()).group(1))")
git tag "$VERSION"
git push --tags || true
