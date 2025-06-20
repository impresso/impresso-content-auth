# Impresso Content Authorization

A service for authorizing access to Impresso content.

## Development

This project uses [Poetry](https://python-poetry.org/) for dependency management and [mypy](http://mypy-lang.org/) for static type checking.

### Setup

```bash
# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Running the server

You can run the server using one of these methods:

1. Using the CLI:

```bash
poetry run impresso-auth --server
```

1. Running the server module directly:

```bash
poetry run python -m impresso_content_auth.server
```

1. Using VS Code's launch configurations (press F5)

### API Endpoints

- Health Check: `GET /health`

### Type Checking

This project uses mypy for static type checking. To run mypy:

```bash
poetry run mypy impresso_content_auth
```

Or use the VS Code task: `Terminal > Run Task > Run mypy`

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. To install the pre-commit hooks:

```bash
poetry run pre-commit install
```

This will run mypy automatically before committing code.

### Code generation

```shell
poetry run datamodel-codegen \
  --input  impresso_content_auth/models/resources/schemas/ \
  --output impresso_content_auth/models/generated \
  --input-file-type jsonschema \
  --output-model-type dataclasses.dataclass \
  --use-field-description \
  --use-schema-description
```

## Docker configuration examples

See the [docker/auth_proxy](docker/auth_proxy) folder for an example of how to run the service in a Docker container and configure it with Nginx.
