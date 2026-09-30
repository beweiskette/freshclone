import argparse
import json
import subprocess
from .readme import read_blocks
from .docker import run
from .safeio import report

def main(argv=None):
    parser = argparse.ArgumentParser(description='Run selected README shell blocks in a restricted fresh Docker container')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('inspect'); p.add_argument('repo')
    p = sub.add_parser('run'); p.add_argument('repo'); p.add_argument('--blocks', required=True)
    p.add_argument('--image', required=True); p.add_argument('--out', required=True)
    p.add_argument('--timeout', type=int, default=120); p.add_argument('--allow-network', action='store_true')
    p.add_argument('--ready-url')
    p.add_argument('--allow-sensitive', action='append', default=[], metavar='TRACKED_PATH')
    p.add_argument('--memory-mib', type=int, default=512)
    p.add_argument('--work-mib', type=int, default=256)
    p.add_argument('--tmp-mib', type=int, default=64)
    p.add_argument('--tmp-exec', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'inspect':
            print(json.dumps(read_blocks(args.repo), indent=2)); return 0
        result = run(args.repo, [int(n) for n in args.blocks.split(',')], args.image, timeout=args.timeout,
                     allow_network=args.allow_network, ready_url=args.ready_url, allow_sensitive=args.allow_sensitive,
                     memory_mib=args.memory_mib, work_mib=args.work_mib, tmp_mib=args.tmp_mib, tmp_exec=args.tmp_exec)
        report(result, args.out)
        print(json.dumps({'status': result['status'], 'cleanup': result['cleanup']}))
        return int(result['status'] != 'pass')
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(2, f'Cannot run verification : {exc}. Check Docker, a local image, selected blocks and safe tracked files.\n')
