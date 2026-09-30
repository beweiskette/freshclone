import subprocess
import uuid
from urllib.parse import urlsplit
from .readme import read_blocks
from .snapshot import snapshot

def docker(*args, **kwargs):
    return subprocess.run(['docker', *args], timeout=kwargs.pop('timeout', 30), **kwargs)

def run(repo, selected, image, *, timeout=120, allow_network=False, ready_url=None,
        allow_sensitive=(), memory_mib=512, work_mib=256, tmp_mib=64, tmp_exec=False):
    available = {b['id']: b for b in read_blocks(repo)}
    if not selected or len(selected) != len(set(selected)) or any(n not in available for n in selected):
        raise ValueError('Select existing, unique README block numbers')
    if not 1 <= timeout <= 600 or not image or image.startswith('-'):
        raise ValueError('Invalid image or timeout')
    if any(type(n) is not int or not 16 <= n <= 16384 for n in (memory_mib, work_mib, tmp_mib)):
        raise ValueError('Memory and tmpfs sizes must be between 16 and 16384 MiB')
    if ready_url:
        url = urlsplit(ready_url)
        if url.scheme != 'http' or url.hostname not in ('localhost', '127.0.0.1', '::1') or url.username or url.password:
            raise ValueError('Readiness URL must be HTTP loopback inside the container')
    payload = snapshot(repo, allow_sensitive=allow_sensitive)
    # Fail before creation if image is absent. Docker must never pull implicitly.
    docker('image', 'inspect', image, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    name = 'freshclone-' + uuid.uuid4().hex
    result = {'schema': 1, 'status': 'fail', 'network': 'enabled' if allow_network else 'disabled',
              'steps': [{'block': n, 'readme_line': available[n]['line'], 'status': 'unreached'} for n in selected],
              'cleanup': False, 'logs': 'First 64 KiB per stream per block; output may contain sensitive data'}
    try:
        docker('create', '--name', name, '--pull=never', '--read-only', '--user', '65534:65534',
               '--cap-drop=ALL', '--security-opt', 'no-new-privileges', '--cpus', '1', '--memory', f'{memory_mib}m',
               '--memory-swap', f'{memory_mib}m', '--pids-limit', '128', '--network', 'bridge' if allow_network else 'none',
               '--tmpfs', f'/work:rw,exec,mode=1777,size={work_mib * 1048576}',
               '--tmpfs', f'/tmp:rw,{"exec" if tmp_exec else "noexec"},mode=1777,size={tmp_mib * 1048576}',
               '--workdir', '/work', '--entrypoint', '/usr/bin/env', image,
               '-i', 'PATH=/usr/local/bin:/usr/bin:/bin', 'HOME=/tmp', '/bin/sh', '-c', 'exec sleep 86400',
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        docker('start', name, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        docker('exec', '-i', name, 'tar', '--no-same-owner', '-xf', '-', '-C', '/work', input=payload,
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for step in result['steps']:
            prefix = '/tmp/freshclone-' + uuid.uuid4().hex
            try:
                child = docker('exec', '-i', name, '/usr/bin/env', '-i', 'PATH=/usr/local/bin:/usr/bin:/bin',
                               'HOME=/tmp', 'LANG=C.UTF-8', '/bin/sh', '-c',
                               f'exec /bin/sh -eu >{prefix}.stdout 2>{prefix}.stderr',
                               input=available[step['block']]['code'].encode(), timeout=timeout,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                step.update(status='pass' if child.returncode == 0 else 'fail', exit_code=child.returncode)
            except subprocess.TimeoutExpired:
                step['status'] = 'timeout'
            # File redirection prevents background children from retaining Docker's
            # attached output pipe. Read only a bounded prefix, including on failure.
            for stream in ('stdout', 'stderr'):
                output = docker('exec', name, 'head', '-c', '65537', f'{prefix}.{stream}',
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                data = output.stdout or b''
                step[stream] = data[:65536].decode('utf-8', errors='replace')
                step[stream + '_truncated'] = len(data) > 65536
            if step['status'] != 'pass':
                break
        if all(s['status'] == 'pass' for s in result['steps']):
            result['status'] = 'pass'
            if ready_url:
                code = '''import urllib.request, sys, time
deadline = time.monotonic() + float(sys.argv[2])
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
while time.monotonic() < deadline:
    try:
        with opener.open(sys.argv[1], timeout=min(1, max(.01, deadline-time.monotonic()))) as response:
            if 200 <= response.status < 400: sys.exit(0)
    except Exception:
        pass
    time.sleep(.1)
sys.exit(1)
'''
                check = docker('exec', name, '/usr/bin/env', '-i', 'PATH=/usr/local/bin:/usr/bin:/bin',
                               'python', '-c', code, ready_url, str(timeout), timeout=timeout+5,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                result['readiness'] = 'pass' if check.returncode == 0 else 'fail'
                result['status'] = result['readiness']
    finally:
        cleanup = docker('rm', '-f', '-v', name, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result['cleanup'] = cleanup.returncode == 0
        if not result['cleanup']:
            result['status'] = 'cleanup-failed'
    return result
