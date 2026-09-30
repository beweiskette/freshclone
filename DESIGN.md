# Version 0.1 design

Check whether selected README commands work in a fresh, restricted Docker container. A failed command is reported with its README block number and source line.

The design was reviewed once through a read-only Claude adapter before implementation. That consultation received feature proposals and synthetic examples, not repository contents or credentials. Implementation and local verification were performed separately; the consultation was a design review, not a code audit.

The selected scope favours explicit user contracts and local evidence. Automatic uploads, model-generated pass criteria, background monitoring and publishing are excluded. This version makes no claim that the idea is unique or that it will attract a particular number of GitHub stars.

## Acceptance evidence

Set `FRESHCLONE_DOCKER_TEST=1` to include real Docker tests after explicitly pulling `python:3.11-slim`. These check success, command failure, network isolation, host environment separation, timeouts and cleanup.

## Deliberate limits

The container runs as UID 65534, with a read-only root filesystem, no capabilities, no host mounts, no Docker socket and a fresh writable `/work`. Limits are 1 CPU, 512 MiB memory and 128 processes. `/work` is limited to 256 MiB and `/tmp` to 64 MiB. Commands receive an explicit small environment instead of host variables.

Tracked working-tree files are streamed into the container. Uncommitted edits to tracked files are included. Untracked files, Git history and Git metadata are excluded. Symlinks, submodules, conflicted entries and common credential filenames are refused. This filename policy is not a secret scanner: manually review tracked source before enabling network access. Maximum snapshot size is 64 MiB, with a 16 MiB per-file limit.

Shell blocks run with `/bin/sh -eu`. Each block gets a new shell; files persist between blocks, while `cd`, exports and shell functions do not. Use one block for a sequence that needs shared shell state. Bash-specific syntax is currently outside scope, even if a fence is labelled `bash`.

Reports omit command output and command text. The first failed or timed-out block stops later blocks. Cleanup is attempted in `finally`; a Docker daemon failure can prevent removal. Docker containers are not a boundary for hostile kernel exploits. Use your own trusted source and image.
