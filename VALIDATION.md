# Validation record

Checked on 2026-09-30 with Python 3.11 on Windows.

Local pytest result: `8 passed, 2 skipped in 5.46s`. Skipped cases require Windows symlink creation privileges; Linux CI exercises those cases. Editable installation, CLI help and wheel construction succeeded. Only synthetic fixtures were used.

The checked-in reports under `examples/` come from actual CLI runs against the synthetic fixtures. Browser reports may contain the temporary loopback port used for that run; adjust the reproduction URL to your running fixture server.

Source review and a staged-file pattern scan found no live credential formats, private user paths or accidentally tracked environment files. This is a scoped check, not a guarantee that every possible secret format is detectable.

Docker/browser integration tests ran locally where applicable.

See the Actions tab for independent Windows and Linux CI results.
