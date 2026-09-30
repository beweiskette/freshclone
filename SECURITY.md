# Data handling

freshclone writes reports to the selected local directory. It has no telemetry or model API integration. HTML reports contain no remote assets.

The container runs as UID 65534, with a read-only root filesystem, no capabilities, no host mounts, no Docker socket and a fresh writable `/work`. Limits are 1 CPU, 512 MiB memory and 128 processes. `/work` is limited to 256 MiB and `/tmp` to 64 MiB. Commands receive an explicit small environment instead of host variables.

Tracked working-tree files are streamed into the container. Uncommitted edits to tracked files are included. Untracked files, Git history and Git metadata are excluded. Symlinks, submodules, conflicted entries and common credential filenames are refused. This filename policy is not a secret scanner: manually review tracked source before enabling network access. Maximum snapshot size is 64 MiB, with a 16 MiB per-file limit.

Shell blocks run with `/bin/sh -eu`. Each block gets a new shell; files persist between blocks, while `cd`, exports and shell functions do not. Use one block for a sequence that needs shared shell state. Bash-specific syntax is currently outside scope, even if a fence is labelled `bash`.

Reports capture bounded command output and omit command text. The first failed or timed-out block stops later blocks. Cleanup is attempted in `finally`; a Docker daemon failure can prevent removal. Docker containers are not a boundary for hostile kernel exploits. Use your own trusted source and image.

Block output and explicitly allowed fixture files can contain secrets. Review them before enabling network access or sharing reports.

GitHub Actions uses read-only repository permissions and publishes no artifacts. Dependency installation contacts package providers. Report security issues privately to the repository owner without live credentials.
