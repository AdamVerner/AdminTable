# Admin Table

## Examples
### Running the examples
First install dependencies neccessary to run the examples
```bash
poetry install --all-groups --no-root
```

Then run the examples
```bash
poetry run python -m example.fastapi_simple
```

### Development
#### Publishing
from root of the project run `./scripts/build.sh` to build the project.
To publish the project to pypi, run `poetry publish`