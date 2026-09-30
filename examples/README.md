# Synthetic FreshClone fixture

Create a tracked example checkout: `git init`, then `git add README.md` inside a copy of this directory.

```sh
python -c "from pathlib import Path; Path('result.txt').write_text('synthetic success')"
```

```sh
test -f result.txt
python -c "from pathlib import Path; assert Path('result.txt').read_text() == 'synthetic success'"
```

Block 3 deliberately demonstrates a missing prerequisite:

```sh
command-that-does-not-exist
```
