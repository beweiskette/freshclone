import subprocess
import uuid
from urllib.parse import urlsplit
from .readme import read_blocks
from .snapshot import snapshot

def docker(*args, **kwargs):
    return subprocess.run(['docker', *args], timeout=kwargs.pop('timeout', 30), **kwargs)

def run(repo, selected, image, *, timeout=120, allow_network=False, ready_url=None):
    available = {b['id']: b for b in read_blocks(repo)}
    if not selected or len(selected) != len(set(selected)) or any(n not in available for n in selected):
        raise ValueError('Select existing, unique README block numbers')
    if not 1 <= timeout <= 600 or not image or image.startswith('-'):
        raise ValueError('Invalid image or timeout')
    if ready_url:
        url = urlsplit(ready_url)
        if url.scheme != 'http' or url.hostname not in ('localhost', '127.0.0.1', '::1') or url.username or url.password:
            raise ValueError('Readiness URL must be HTTP loopback inside the container')
    payload = snapshot(repo)
    # Fail before creation if image is absent. Docker must never pull implicitly.
    docker('image', 'inspect', image, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    name = 'freshclone-' + uuid.uuid4().hex
    result = {'schema': 1, 'status': 'fail', 'network': 'enabled' if allow_network else 'disabled',
              'steps': [{'block': n, 'readme_line': available[n]['line'], 'status': 'unreached'} for n in selected],
              'cleanup': False, 'logs': 'not captured'}
    try:
        docker('create', '--name', name, '--pull=never', '--read-only', '--user', '65534:65534',
               '--cap-drop=ALL', '--security-opt', 'no-new-privileges', '--cpus', '1', '--memory', '512m',
               '--memory-swap', '512m', '--pids-limit', '128', '--network', 'bridge' if allow_network else 'none',
               '--tmpfs', '/work:rw,exec,mode=1777,size=268435456', '--tmpfs', '/tmp:rw,noexec,mode=1777,size=67108864',
               '--workdir', '/work', '--entrypoint', '/usr/bin/env', image,
               '-i', 'PATH=/usr/local/bin:/usr/bin:/bin', 'HOME=/tmp', '/bin/sh', '-c', 'exec sleep 86400',
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        docker('start', name, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        docker('exec', '-i', name, 'tar', '--no-same-owner', '-xf', '-', '-C', '/work', input=payload,
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for step in result['steps']:
            try:
                child = docker('exec', '-i', name, '/usr/bin/env', '-i', 'PATH=/usr/local/bin:/usr/bin:/bin',
                               'HOME=/tmp', 'LANG=C.UTF-8', '/bin/sh', '-eu',
                               input=available[step['block']]['code'].encode(), timeout=timeout,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                step.update(status='pass' if child.returncode == 0 else 'fail', exit_code=child.returncode)
            except subprocess.TimeoutExpired:
                step['status'] = 'timeout'
            if step['status'] != 'pass':
                break
        if all(s['status'] == 'pass' for s in result['steps']):
            result['status'] = 'pass'
            if ready_url:
                code = 'import urllib.request,sys; r=urllib.request.urlopen(sys.argv[1],timeout=5); assert 200 <= r.status < 400'
                check = docker('exec', name, '/usr/bin/env', '-i', 'PATH=/usr/local/bin:/usr/bin:/bin',
                               'python', '-c', code, ready_url, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                result['readiness'] = 'pass' if check.returncode == 0 else 'fail'
                result['status'] = result['readiness']
    finally:
        cleanup = docker('rm', '-f', name, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result['cleanup'] = cleanup.returncode == 0
        if not result['cleanup']:
            result['status'] = 'cleanup-failed'
    return result
