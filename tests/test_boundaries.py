from pathlib import Path
import pytest
from freshclone.safeio import local_path, report

@pytest.mark.parametrize("value", [r"\\untrusted.invalid\share\secret", "//server/share", "https://example.com/a"])
def test_network_paths_refused(value):
    with pytest.raises(ValueError):
        local_path(value)

def test_report_escapes_markup_and_stays_local(tmp_path):
    report({"name": "<script>alert(1)</script>"}, tmp_path)
    html = (tmp_path / 'report.html').read_text()
    assert '<script>' not in html
    assert '&lt;script&gt;' in html

def test_link_refused(tmp_path):
    target = tmp_path / 'target'
    target.write_text('private')
    link = tmp_path / 'link'
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip('OS does not allow creating symlinks')
    with pytest.raises(ValueError):
        local_path(link)
