# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`cloud-fusion` (formerly `aws-fusion`) is a Python CLI that bundles cloud provider authentication / convenience helpers behind one entry point, organized by provider so more clouds can be added alongside AWS. Published to PyPI as `cloud-fusion`; the version lives in `cloud_fusion/__init__.py` and is what triggers a publish (see CI section).

## Development

```shell
pip install -e .        # editable install — pulls deps from pyproject.toml
cloud-fusion --help     # console_scripts entry point → cloud_fusion.app:main
python -m cloud_fusion.app --help   # equivalent invocation used by the `aws fusion` alias
```

There is no test suite, lint config, or formatter wired up. Don't fabricate one.

## Architecture

Entry point flow: `cloud_fusion/app.py` builds an `argparse` parser, then registers each provider package under `cloud_fusion/providers/`. Every provider package exposes a `setup(subparsers, parent_parser)` function that registers a `<provider>` subparser and delegates to its own `commands/` package; each command module in there exposes the same `setup(subparsers, parent_parser)` convention one level down, binding `args.func` to a `run` callable. `--debug` is a global flag handled in `app.py`.

To add a new cloud provider: create `cloud_fusion/providers/<provider>/` with an `__init__.py` that defines `setup(subparsers, parent_parser)` — registering a `<provider>` subparser and delegating to a sibling `commands/` package the same way `providers/aws/__init__.py` does — then append the package to the `commands` list in `app.py`. Provider-specific modules stay entirely inside that provider's directory; nothing outside `providers/<provider>/` should import from it. There is currently no provider-neutral top-level command; if one is ever needed, add a `cloud_fusion/commands/` package following the same `setup(subparsers, parent_parser)` convention and register it alongside the provider packages in `app.py`.

All cross-module imports are relative (`from ...exceptions import CloudFusionException`, `from ..api import signin_url`, etc.) — depth tracks nesting under `providers/<provider>/`.

AWS provider (`cloud_fusion/providers/aws/`) subcommands and what they wrap — invoked as `cloud-fusion aws <command>`:

- `init` — writes a `[toplevel] fusion = !"<python>" -m cloud_fusion.app aws` entry into `~/.aws/cli/alias` so `aws fusion ...` proxies to `cloud-fusion aws ...`.
- `open-browser` — `providers/aws/commands/open_browser.py` → `providers/aws/session.py` resolves boto3 credentials (and rewires the assume-role / sso credential providers to use `~/.aws/cli/cache` so caching matches the AWS CLI) → `providers/aws/api.py` exchanges them for a federation signin token and builds a console signin URL. Requires session credentials (`creds.token` must be non-null), so it only works for assume-role / SSO / federated profiles, not raw IAM user keys.
- `iam-user-credentials store|get` — stores/retrieves secret keys via `keyring` (OS credential store). Service name is `aws-<account-id>-<username>`, username field is the access key. `get --credential-process` emits the JSON shape AWS CLI expects for `credential_process`.
- `config-switch profile|region` — interactive `inquirer` picker that writes the chosen value to `~/.aws/fusion/profile` or `~/.aws/fusion/region`. These files are read by the `bin/_awsp` / `bin/_awsr` shell scripts (and `.ps1` equivalents), which run `cloud-fusion aws config-switch ...` then `export AWS_PROFILE` / `AWS_REGION` in the caller's shell. The scripts must be sourced (e.g. `alias awsp="source _awsp"`) — running them as a child process has no effect.

`~/.aws/cli/cache` (AWS CLI–compatible) is used by `open-browser` for boto3's built-in credential providers. It stays under `~/.aws/` even after the rename — no state migration was done, so existing installs keep working unchanged.

GCP provider (`cloud_fusion/providers/gcp/`) — invoked as `cloud-fusion gcp <command>`:

- `config-switch configuration|region` — interactive `inquirer` picker, same UX as the AWS one, but choices are enumerated by shelling out to `gcloud` (`providers/gcp/gcloud.py` wraps `subprocess`, never parses `~/.config/gcloud/` directly) and the selection is applied **globally** via `gcloud config configurations activate` / `gcloud config set compute/region` — unlike AWS, there's no per-shell state file. `configuration` also runs `gcloud auth application-default set-quota-project` on the newly active project (best-effort; skip with `--skip-quota-project`). `bin/_gcpc` / `bin/_gcpr` (and `.ps1` equivalents) are thin wrappers around `cloud-fusion gcp config-switch configuration|region` — they do **not** need to be sourced, since the mutation already happened inside the `cloud-fusion` process and there's no env var to export back into the caller's shell.

## Release / CI

`.github/workflows/publish.yml` is the only workflow. It runs on:
- `push` to `main` **only when `cloud_fusion/__init__.py` changes** → publishes to real PyPI and pushes a `v<version>` git tag.
- `pull_request` to `main` or manual `workflow_dispatch` → publishes to **Test** PyPI with a version suffixed by `.<github.run_number>`.

So bumping `__version__` in `cloud_fusion/__init__.py` on `main` is the release trigger. Don't bump it casually.

The `[tool.hatch.build.targets.wheel.shared-scripts]` table in `pyproject.toml` installs `bin/_awsp`, `bin/_awsr`, `bin/_gcpc`, `bin/_gcpr`, and their `.ps1` siblings onto the user's PATH — keep that table in sync if new shell helpers are added. Each provider's scripts carry that provider's prefix (`_aws*`, `_gcp*`), unlike the rest of the CLI.
