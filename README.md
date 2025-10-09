# time-series

Time-series supergroup

## Project structure

This project follows the core structure of [Polylith](https://davidvujic.github.io/python-polylith-docs/).

At a high level, it means the project is structured into 3 major folders.

- `bases/` which hold __executable__/__runnable__ code. Think of it as FastAPI entrypoint, or a CLI entrypoint.
- `components/` which hold all __library__ code. This is where business logic will go.
- `projects/` which hold a `pyproject.toml` that collects up bases and components. It holds no code.

This structure can also be seen in the `test` folders.

You can have a scratch file in `development/`, which imports all components. This is a great way to start out,
you may also commit this to the repo freely.

```bash
uv run development/file.py
```

### How to make a new base/component

Either you can make a new folder in `bases/` or `components/` with a `__init__.py` file to mark it as a library.
Finally you need to add a line to your `projects/` that should import it, as well as the top level `pyproject.toml`

Also add a poe hook to allow using it from the top level

```toml
#pyproject.toml
[tool.poe.tasks]
...
rest_api = "poe -C projects/rest_api"
```

This could look like the following:

```toml
# /pyproject.toml
[tool.polylith.bricks]
"bases/time_series/rest_api" = "time_series/rest_api"
"components/time_series/greeting" = "time_series/greeting"
```

You may also use the `poly` tool directly to do this as well, but this is only to help do this more quickly.

```bash
poly create component --name example
poly create base --name example
poly sync # To add the new bricks to prproject.toml
```

### How to make a new project

Mainly look at the other projects. Most of this is just scaffholding. It should contain a `pyproject.toml` which imports
the components it is using. It may also include items such as a `Containerfile`.

> [!TIP]
> Polylith does dependency version resolution by taking the intersection of all project's version requirements.
>
> To simplify version management, set all dependency versions in `projects/name/pyproject.toml` to `>0` and instead
> manage it in the root `pyproject.toml`. When building, this will use the version in the root to select the
> version.

## Development

Install `uv` through your favorite package manager, then run:

```bash
uv run poe setup
source .venv/bin/activate
```

This will install all dependencies and set up virtualenv and pre-commit.

> [!TIP]
> You may also configure `direnv` and write `direnv allow` once in this repo to do this
> automatically at folder entry.

### Getting dangerous with `uv`

```bash
uv add <dependency_name> # To install a runtime dependency
uv add --dev <dependency_name> # To install a developer only dependency
```

### Getting dangerous with `poe`

Poe the Poet is a task executor. It holds aliases to common shell commands.

```bash
poe # Lists all configured shell commands.
poe test # To run pytest on the whole project.
poe all # To run all linters, formatters, and checkers.
poe <project_name> # To list configured shell commands for a project.
poe <project_name> serve # To start uvicorn for that project.
```

### Getting dangerous with `podman`

You may also use `docker` as an alternative.

```bash
podman build -t <project_name>:latest -f Containerfile ../.. # inside the project folder
podman run -it --name project_name <project_name>:latest -p 8000:8000
```

Alternatively you can use `poe` as well to do this.

```bash
poe <project_name> container-build
poe <project_name> container-run
```

### Getting dangerous with `poly`

```bash
poly info # To show which bricks are imported in which projects.
poly sync # To add bricks to pyproject.toml automatically.
poly create base # To create a new base (executable) brick.
poly create component # To create a new component (library) brick.
```
