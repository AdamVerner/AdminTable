#!/usr/bin/env bash

set -e
set -x

# build ui
cd ui && yarn build && cd ..

# copy ui into package
rm -r table_api/ui
cp -r ui/dist table_api/ui

# build python wheel and dist
poetry build
zipinfo dist/*.whl
