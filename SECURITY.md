# Data handling

FreshClone has no telemetry, update checks, cloud account or model API integration. Reports are written only to the chosen local output directory. HTML uses no remote scripts, fonts or images.

The container runs as UID 65534, with a read-only root filesystem, no capabilities, no host mounts, no Docker socket and a fresh writable `/work`. Limits are 1 CPU, 512 MiB memory and 128 processes. `/work` is limited to 256 MiB and `/tmp` to 64 MiB. Commands receive an explicit small environment instead of host variables.

Tracked working-tree files are streamed into the container. Uncommitted edits to tracked files are included. Untracked files, Git history and Git metadata are excluded. Symlinks, submodules, conflicted entries and common credential filenames are refused. This filename policy is not a secret scanner: manually review tracked source before enabling network access. Maximum snapshot size is 64 MiB, with a 16 MiB per-file limit.

Shell blocks run with `/bin/sh -eu`. Each block gets a new shell; files persist between blocks, while `cd`, exports and shell functions do not. Use one block for a sequence that needs shared shell state. Bash-specific syntax is currently outside scope, even if a fence is labelled `bash`.

Reports omit command output and command text. The first failed or timed-out block stops later blocks. Cleanup is attempted in `finally`; a Docker daemon failure can prevent removal. Docker containers are not a boundary for hostile kernel exploits. Use your own trusted source and image.

Dependencies are installed separately from package providers. GitHub Actions checks out the source and runs the test suite on GitHub-hosted runners. Workflows receive read-only repository permissions and publish no artifacts. Review inputs and reports before sharing them. Keep synthetic examples in this repository; do not commit real credentials, exports or receipts.

If you find a security issue, report it privately to the repository owner without including live credentials or personal data.
