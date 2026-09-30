# Validation

Checked on 2026-09-30 with Python 3.11 on Windows.

Before these repairs: 10 collected tests. After: 20 collected, 18 passed and 2 skipped. The skipped cases require Windows symlink creation privileges. Linux CI runs those cases. New bug regressions were run against the previous implementation and observed failing before their fixes; the XML test strengthens existing escaping coverage.

Real Docker tests cover delayed readiness, captured output, anonymous-volume removal, command failure, timeout, network isolation and host-environment separation.

The current wheel builds with `python -m pip wheel --no-deps .` using pip's isolated build environment. CLI help succeeds. German README validation with schreibwaechter and locale de-CH reports 0 errors and 0 warnings. Only synthetic test inputs were used.

CI results are available at [GitHub Actions](https://github.com/beweiskette/freshclone/actions). See SECURITY.md for report contents and runtime boundaries.
