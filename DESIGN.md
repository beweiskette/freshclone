# Design

Verify README shell commands in disposable, restricted Docker containers.

README fences accept a language followed by metadata, such as `sh title="setup"`. Only sh, shell and bash blocks are selected; all execute with `/bin/sh -eu`. Tracked UTF-8 text without NUL bytes is converted from CRLF to LF in the snapshot. Binary bytes are preserved.

Credential-like filenames remain blocked by default. To include reviewed examples or fixtures, repeat an exact tracked relative path: `--allow-sensitive .env.example --allow-sensitive tests/fixture.pem`. This also permits real secrets at those paths, so inspect their contents first.

Use `--memory-mib`, `--work-mib` and `--tmp-mib` to increase the default 512, 256 and 64 MiB budgets. Each accepts 16 to 16384 MiB. `--tmp-exec` permits execution in `/tmp` when a build needs it. Installing dependencies also needs the explicit `--allow-network` option and sufficient memory. No host caches or credentials are mounted.

Readiness retries every 100 ms for up to `--timeout` seconds after the blocks pass. Background server processes can continue inside the container. The image also needs `head` to collect output. Each block report contains the first 64 KiB of stdout and stderr plus truncation flags. Live log files consume the configured `/tmp` budget. Output is collected at the end of each block and can contain secrets; review reports before sharing them. Cleanup removes the container and its anonymous volumes, including volumes declared by the image.

## Scope

The container runs as UID 65534, with a read-only root filesystem, no capabilities, no host mounts, no Docker socket and a fresh writable `/work`. Limits are 1 CPU, 512 MiB memory and 128 processes. `/work` is limited to 256 MiB and `/tmp` to 64 MiB. Commands receive an explicit small environment instead of host variables.

Tracked working-tree files are streamed into the container. Uncommitted edits to tracked files are included. Untracked files, Git history and Git metadata are excluded. Symlinks, submodules, conflicted entries and common credential filenames are refused. This filename policy is not a secret scanner: manually review tracked source before enabling network access. Maximum snapshot size is 64 MiB, with a 16 MiB per-file limit.

Shell blocks run with `/bin/sh -eu`. Each block gets a new shell; files persist between blocks, while `cd`, exports and shell functions do not. Use one block for a sequence that needs shared shell state. Bash-specific syntax is currently outside scope, even if a fence is labelled `bash`.

Reports capture bounded command output and omit command text. The first failed or timed-out block stops later blocks. Cleanup is attempted in `finally`; a Docker daemon failure can prevent removal. Docker containers are not a boundary for hostile kernel exploits. Use your own trusted source and image.
