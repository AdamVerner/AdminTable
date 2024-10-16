#!/usr/bin/env bash

set -e
set -x

# check python code style
ruff format
ruff check --fix

# build ui
cd ui
yarn run prettier:write
cd ..
