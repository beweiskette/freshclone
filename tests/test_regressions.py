import io
import subprocess
import tarfile
import pytest
from test_freshclone import repo
from freshclone.readme import blocks
from freshclone.snapshot import snapshot
from freshclone import cli
import freshclone.docker as engine

def test_fence_metadata_does_not_swallow_next_block():
    result = blocks('```sh title="x"\necho one\n```\n```sh\necho two\n```\n')
    assert [b['code'] for b in result] == ['echo one\n', 'echo two\n']

def test_snapshot_normalises_crlf_but_preserves_binary(tmp_path):
    repo(tmp_path, '# test')
    (tmp_path/'run.sh').write_bytes(b'#!/bin/sh\r\necho ok\r\n')
    (tmp_path/'binary').write_bytes(b'\0\r\n')
    subprocess.run(['git','-C',str(tmp_path),'add','.'], check=True)
    with tarfile.open(fileobj=io.BytesIO(snapshot(tmp_path))) as tar:
        assert tar.extractfile('run.sh').read() == b'#!/bin/sh\necho ok\n'
        assert tar.extractfile('binary').read() == b'\0\r\n'

def test_sensitive_fixture_requires_exact_opt_in(tmp_path):
    repo(tmp_path, '# test')
    for name in ('.env.example', 'fixture.pem', '.env'):
        (tmp_path/name).write_text('SYNTHETIC')
    subprocess.run(['git','-C',str(tmp_path),'add','.'], check=True)
    with pytest.raises(ValueError, match='Sensitive'):
        snapshot(tmp_path, allow_sensitive=['.env.example', 'fixture.pem'])
    data = snapshot(tmp_path, allow_sensitive=['.env.example', 'fixture.pem', '.env'])
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        assert '.env.example' in tar.getnames()

def test_cli_error_has_reason(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(['inspect',str(tmp_path)])
    assert error.value.code == 2
    assert 'README.md not found' in capsys.readouterr().err

def test_cleanup_removes_anonymous_volumes(tmp_path, monkeypatch):
    root = repo(tmp_path, '```sh\necho marker\n```')
    calls = []
    def fake(*args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout=b'marker\n', stderr=b'')
    monkeypatch.setattr(engine, 'docker', fake)
    result = engine.run(root,[1],'local-image')
    removal = next(c for c in calls if c[0] == 'rm')
    assert '-v' in removal
    assert result['cleanup']

def test_block_output_is_captured(tmp_path, monkeypatch):
    root = repo(tmp_path, '```sh\necho marker\n```')
    monkeypatch.setattr(engine, 'docker', lambda *a, **kw: subprocess.CompletedProcess(a,0,stdout=b'marker\n',stderr=b''))
    result = engine.run(root,[1],'local-image')
    assert result['steps'][0]['stdout'] == 'marker\n'

def test_resource_options_are_applied(tmp_path, monkeypatch):
    root = repo(tmp_path, '```sh\ntrue\n```')
    calls = []
    def fake(*args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args,0,stdout=b'',stderr=b'')
    monkeypatch.setattr(engine, 'docker', fake)
    engine.run(root,[1],'local-image',memory_mib=1024,work_mib=512,tmp_mib=128,tmp_exec=True)
    create = next(c for c in calls if c[0]=='create')
    assert '1024m' in create
    assert '/tmp:rw,exec,mode=1777,size=134217728' in create

@pytest.mark.integration
def test_delayed_background_readiness_and_output(tmp_path):
    import os
    if not os.environ.get('FRESHCLONE_DOCKER_TEST'): pytest.skip('Docker integration disabled')
    root = repo(tmp_path, '```sh\n(sleep 2; python -m http.server 8765 --bind 127.0.0.1) >/tmp/server.log 2>&1 &\necho started\n```')
    result = engine.run(root,[1],'python:3.11-slim',timeout=4,ready_url='http://127.0.0.1:8765')
    assert result['status'] == 'pass', result
    assert 'started' in result['steps'][0]['stdout']
    assert result['cleanup']

@pytest.mark.integration
def test_real_anonymous_volume_removed(tmp_path,monkeypatch):
    import os, json
    if not os.environ.get('FRESHCLONE_DOCKER_TEST'): pytest.skip('Docker integration disabled')
    real=engine.docker
    volumes=[]
    def tracking(*args,**kwargs):
        if args[0]=='create':
            args=(args[0],'--volume','/synthetic-volume',*args[1:])
            result=real(*args,**kwargs)
            name=args[args.index('--name')+1]
            info=real('inspect',name,capture_output=True,check=True)
            volumes.extend(m['Name'] for m in json.loads(info.stdout)[0]['Mounts'] if m['Type']=='volume')
            return result
        return real(*args,**kwargs)
    monkeypatch.setattr(engine,'docker',tracking)
    root=repo(tmp_path,'```sh\ntrue\n```')
    result=engine.run(root,[1],'python:3.11-slim')
    assert result['cleanup'] and volumes
    for volume in volumes:
        assert real('volume','inspect',volume,capture_output=True).returncode != 0

@pytest.mark.integration
def test_large_build_file_within_resource_budget(tmp_path):
    import os
    if not os.environ.get('FRESHCLONE_DOCKER_TEST'): pytest.skip('Docker integration disabled')
    root=repo(tmp_path,'```sh\npython -c "open(\'build.bin\',\'wb\').write(b\'x\' * 2097152)"\n```')
    result=engine.run(root,[1],'python:3.11-slim')
    assert result['status']=='pass', result
