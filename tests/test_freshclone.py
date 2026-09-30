import os
import subprocess
import pytest
from freshclone.readme import blocks
from freshclone.snapshot import snapshot
from freshclone.docker import run

def repo(tmp_path, body):
    (tmp_path / 'README.md').write_text(body)
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(['git', '-C', str(tmp_path), 'add', 'README.md'], check=True)
    return tmp_path

def test_fence_lines_and_ignore_other_languages():
    result = blocks('# Hi\n\n```bash\necho hello\n```\n```python\nprint(1)\n```\n')
    assert result == [{'id': 1, 'line': 4, 'code': 'echo hello\n'}]

def test_tracked_secrets_refused(tmp_path):
    repo(tmp_path, '# hi')
    (tmp_path / '.env').write_text('SYNTHETIC_SECRET')
    subprocess.run(['git', '-C', str(tmp_path), 'add', '.env'], check=True)
    with pytest.raises(ValueError):
        snapshot(tmp_path)

@pytest.mark.integration
def test_real_container_steps_privacy_and_timeout(tmp_path, monkeypatch):
    if not os.environ.get('FRESHCLONE_DOCKER_TEST'):
        pytest.skip('Set FRESHCLONE_DOCKER_TEST=1 with python:3.11-slim available')
    monkeypatch.setenv('SYNTHETIC_HOST_SECRET', 'not-for-container')
    body = '''```bash
test -z "${SYNTHETIC_HOST_SECRET:-}"
test "$(id -u)" = 65534
python -c "import socket; s=socket.socket(); s.settimeout(1); assert s.connect_ex(('1.1.1.1',443)) != 0"
echo ok > state
```
```bash
test -f state
exit 7
```
```bash
echo should-not-run
```
'''
    root = repo(tmp_path, body)
    result = run(root, [1, 2, 3], 'python:3.11-slim', timeout=10)
    assert [s['status'] for s in result['steps']] == ['pass', 'fail', 'unreached']
    assert result['steps'][1]['exit_code'] == 7
    assert result['cleanup'] is True
    success = run(root, [1], 'python:3.11-slim', timeout=10)
    assert success['status'] == 'pass' and success['cleanup'] is True
    (root / 'README.md').write_text('```bash\nsleep 30\n```\n')
    result = run(root, [1], 'python:3.11-slim', timeout=1)
    assert result['steps'][0]['status'] == 'timeout'
    assert result['cleanup'] is True

def test_snapshot_rejects_outside_symlink(tmp_path):
    repo(tmp_path, '# demo')
    outside = tmp_path.parent / 'outside-synthetic.txt'
    outside.write_text('SYNTHETIC_PRIVATE')
    try:
        (tmp_path / 'link').symlink_to(outside)
    except OSError:
        pytest.skip('OS does not allow symlinks')
    subprocess.run(['git', '-C', str(tmp_path), 'add', 'link'], check=True)
    with pytest.raises(ValueError): snapshot(tmp_path)

def test_invalid_selection_before_docker(tmp_path):
    root = repo(tmp_path, '```sh\necho hi\n```')
    with pytest.raises(ValueError):
        run(root, [999], 'no-image')
