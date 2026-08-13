This project uses [uv](https://docs.astral.sh/uv/) for environment and dependency management. Python 3.12 is required.

```shell
git clone https://github.com/snigdhasjg/cloud-fusion.git
cd cloud-fusion
uv sync                          # create .venv and install deps + project (editable)
uv run cloud-fusion --help       # run the CLI from the project venv
```

To build distributions locally:

```shell
uv build                         # produces dist/*.whl and dist/*.tar.gz
```
