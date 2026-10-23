"""Keep public product copy and repository links consistent after a rename."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = 'Local Token Buffet Bridge'
REPOSITORY = 'local-token-buffet-bridge'


def violations(name, text):
    # The repository owner is a GitHub namespace, not the product brand.
    text = text.replace('AI-GO-APP/', 'repository-owner/')
    errors = []
    if re.search(r'\bai[\s_-]+go\b', text, re.I):
        errors.append('retired product attribution')
    if re.search(r'\bai-go\.app\b', text, re.I):
        errors.append('retired platform installation instructions')
    if re.search(r'(?:github\.com|githubusercontent\.com)/[^/\s]+/aigo-llm-bridge(?:[/\s.)]|$)', text):
        errors.append('old repository link')
    return [name + ': ' + error for error in errors]


def check(root=ROOT):
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    errors = []
    for name in names:
        path = root / name
        public = path.suffix == '.md' or name == 'LICENSE' or name.startswith('desktop_bridge/web/')
        if public and path.is_file():
            errors.extend(violations(name, path.read_text(encoding='utf-8')))
    for name in ('README.md', 'desktop_bridge/web/index.html'):
        if PRODUCT not in (root / name).read_text(encoding='utf-8'):
            errors.append(name + ': missing product name')
    return errors


if __name__ == '__main__':
    errors = check()
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print('Product branding and repository links: passed.')
