# FreshClone

Check whether selected README commands work in a fresh, restricted Docker container. A failed command is reported with its README block number and source line.

Version 0.1.0. [Deutsch](README.de.md). Python 3.11 or newer. MIT licence.

## Install

From a clone of this repository:

```sh
python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell instead:
# .\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
```

## Run

```sh
freshclone inspect ./your-project
freshclone run ./your-project --blocks 1,2 --image python:3.11-slim --out outputs/check
```

Copy `examples/README.md` into a new directory, run `git init` and `git add README.md` there, then use that directory as `./your-project`. Blocks 1 and 2 pass; block 3 deliberately calls a missing command.

Install Docker and explicitly pull a trusted Linux image first, for example `docker pull python:3.11-slim`. FreshClone never pulls images. The image must contain `/bin/sh`, `/usr/bin/env`, `sleep`, and GNU `tar`. The readiness check additionally needs `python` with its standard library.

`--timeout 120` sets a per-block limit (1 to 600 seconds). `--ready-url http://127.0.0.1:8000/` checks HTTP from inside the container after all blocks pass. `--allow-network` explicitly enables Docker bridge networking, including any destinations reachable from the container.

Reports are local JSON and self-contained HTML. Exit status is 0 for a pass, 1 for findings, and 2 for an input or runtime setup error. Commands do not publish reports or contact a model API.

## Boundaries

The container runs as UID 65534, with a read-only root filesystem, no capabilities, no host mounts, no Docker socket and a fresh writable `/work`. Limits are 1 CPU, 512 MiB memory and 128 processes. `/work` is limited to 256 MiB and `/tmp` to 64 MiB. Commands receive an explicit small environment instead of host variables.

Tracked working-tree files are streamed into the container. Uncommitted edits to tracked files are included. Untracked files, Git history and Git metadata are excluded. Symlinks, submodules, conflicted entries and common credential filenames are refused. This filename policy is not a secret scanner: manually review tracked source before enabling network access. Maximum snapshot size is 64 MiB, with a 16 MiB per-file limit.

Shell blocks run with `/bin/sh -eu`. Each block gets a new shell; files persist between blocks, while `cd`, exports and shell functions do not. Use one block for a sequence that needs shared shell state. Bash-specific syntax is currently outside scope, even if a fence is labelled `bash`.

Reports omit command output and command text. The first failed or timed-out block stops later blocks. Cleanup is attempted in `finally`; a Docker daemon failure can prevent removal. Docker containers are not a boundary for hostile kernel exploits. Use your own trusted source and image.

## Verify

```sh
python -m pytest -q
```

Set `FRESHCLONE_DOCKER_TEST=1` to include real Docker tests after explicitly pulling `python:3.11-slim`. These check success, command failure, network isolation, host environment separation, timeouts and cleanup.

GitHub Actions runs tests on Windows and Linux. Integration jobs use synthetic local fixtures. No deployment or package publication workflow is configured. Dependency installation and browser/image downloads are explicit setup steps that contact their respective package providers.

See [DESIGN.md](DESIGN.md) for the scope decisions and [SECURITY.md](SECURITY.md) for data handling.
