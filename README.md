# Admin Table

## Examples
### Running the examples
First install dependencies neccessary to run the examples
```bash
pip install admin_table
pip install uvicorn sqlalchemy fastapi[standard]
```

Then run the examples
```bash
poetry run python examples/fastapi_simple.py
```

### Development
#### Publishing
from root of the project run `./scripts/build.sh` to build the project and publish it.
To publish the project to pypi, run `poetry publish`