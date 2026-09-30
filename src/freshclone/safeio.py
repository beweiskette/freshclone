"""Local file boundaries and reports. No network operations."""
import html
import json
import os
from pathlib import Path

def local_path(value, *, exists=True):
    raw = str(value)
    if raw.startswith(('\\\\', '//')) or '://' in raw:
        raise ValueError('A local path is required; UNC and URL paths are refused')
    p = Path(os.path.abspath(raw))
    for part in [*reversed(p.parents), p]:
        if part.is_symlink():
            raise ValueError('Symbolic links are refused')
        try:
            if getattr(part.lstat(), 'st_file_attributes', 0) & 0x400:
                raise ValueError('Windows reparse points are refused')
        except FileNotFoundError:
            if exists:
                raise ValueError('Input does not exist') from None
    if exists and not p.exists():
        raise ValueError('Input does not exist')
    return p

def read_json(path):
    p = local_path(path)
    if p.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('JSON input exceeds 8 MiB')
    return json.loads(p.read_text(encoding='utf-8-sig'))

def report(data, directory):
    out = local_path(directory, exists=False)
    out.mkdir(parents=True, exist_ok=True)
    for name in ('report.json', 'report.html'):
        local_path(out / name, exists=False)
    body = json.dumps(data, ensure_ascii=False, indent=2)
    (out / 'report.json').write_text(body + '\n', encoding='utf-8')
    (out / 'report.html').write_text(
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">'
        '<title>Local verification report</title><style>body{max-width:1000px;margin:3rem auto;padding:1rem;'
        'font:16px system-ui;background:#101923;color:#eaf2fa}pre{white-space:pre-wrap;overflow-wrap:anywhere;'
        'background:#192838;padding:1.5rem;border-radius:12px}h1{color:#9bd9cd}</style>'
        '<h1>Local verification report</h1><pre>' + html.escape(body) + '</pre>', encoding='utf-8')
    return out
