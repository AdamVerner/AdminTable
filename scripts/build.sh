#!/usr/bin/env bash

set -e
set -x

# check python code style and types
ruff check
mypy admin_table

# build ui
cd ui
yarn test
yarn build
cd ..

# copy ui into package
rm -rf admin_table/ui
cp -r ui/dist admin_table/ui

# build python wheel and dist
poetry build
zipinfo dist/*.whl
