import io
from pathlib import PurePosixPath
import subprocess
import tarfile
from .safeio import local_path

def snapshot(repo, *, allow_sensitive=()):
    root = local_path(repo)
    result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(root), 'ls-files', '--stage', '-z'], capture_output=True, check=True, timeout=30)
    buffer, total = io.BytesIO(), 0
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        for record in result.stdout.split(b'\0'):
            if not record:
                continue
            meta, raw = record.split(b'\t', 1)
            mode, _, stage = meta.decode('ascii').split()
            name = raw.decode('utf-8')
            parts = PurePosixPath(name).parts
            if mode not in ('100644', '100755') or stage != '0' or '..' in parts or name.startswith('/') or '\\' in name or ':' in name:
                raise ValueError('Unsupported Git entry')
            lowered = [part.lower() for part in parts]
            if any(part in ('.git', '.ssh', '.aws', '.azure', '.npmrc', '.pypirc', 'credentials.json', 'id_rsa', 'id_ed25519') or part == '.env' or part.startswith('.env.') or part.endswith(('.pem', '.p12', '.pfx', '.key')) for part in lowered):
                if name not in allow_sensitive:
                    raise ValueError(f'Sensitive filename is tracked: {name}. Review it, then explicitly allow it with --allow-sensitive {name}')
            path = local_path(root / name)
            size = path.stat().st_size
            total += size
            if size > 16 * 1024 * 1024 or total > 64 * 1024 * 1024:
                raise ValueError('Snapshot size limit exceeded')
            data = path.read_bytes()
            if b'\0' not in data:
                try:
                    data.decode('utf-8')
                except UnicodeDecodeError:
                    pass
                else:
                    data = data.replace(b'\r\n', b'\n')
            info = tarfile.TarInfo(name)
            info.size, info.uid, info.gid, info.mode = len(data), 65534, 65534, 0o755 if mode == '100755' else 0o644
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()
