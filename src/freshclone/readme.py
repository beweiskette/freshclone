import re
from .safeio import local_path

def blocks(text):
    result, fence, code, start, accepted = [], None, [], 0, False
    for line_no, line in enumerate(text.splitlines(keepends=True), 1):
        if fence is None:
            match = re.match(r'^ {0,3}(`{3,}|~{3,})([\w-]*)\s*$', line.rstrip())
            if match:
                fence = match[1]
                accepted = match[2].lower() in ('bash', 'sh', 'shell')
                start, code = line_no + 1, []
        elif re.match(r'^ {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*$', line.rstrip()):
            if accepted:
                result.append({'id': len(result) + 1, 'line': start, 'code': ''.join(code)})
            fence = None
        else:
            code.append(line)
    if fence is not None and accepted:
        raise ValueError('Unclosed shell code fence')
    return result

def read_blocks(repo):
    root = local_path(repo)
    for name in ('README.md', 'readme.md', 'Readme.md'):
        path = root / name
        if path.exists():
            local_path(path)
            if path.stat().st_size > 1024 * 1024:
                raise ValueError('README exceeds 1 MiB')
            return blocks(path.read_text(encoding='utf-8-sig'))
    raise ValueError('README.md not found')
