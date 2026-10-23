"""Check product docs against schema, API and CSS using synthetic SQLite only."""
import ast
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check(root=ROOT):
    from desktop_bridge.store import DEFAULTS, Store
    names = ('README', 'REQUIREMENTS', 'ARCHITECTURE', 'SCHEMA', 'API',
             'DESIGN-SYSTEM', 'DECISIONS', 'ACCEPTANCE', 'ONBOARDING', 'CI-CD', 'RELEASE')
    errors, documents = [], {}
    for name in names:
        path = root / 'docs' / (name + '.md')
        if not path.is_file():
            errors.append('Missing product document: ' + name)
        else:
            documents[name] = path.read_text(encoding='utf-8')
    if errors:
        return errors
    for name, text in documents.items():
        outside_code = re.sub(r'```.*?```|~~~.*?~~~', '', text, flags=re.S)
        for target in re.findall(r'\]\(([^)\s]+)\)', outside_code):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = (root / 'docs' / unquote(parsed.path)).resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                errors.append('Broken product link in ' + name + ': ' + target)
    with tempfile.TemporaryDirectory(prefix='bridge-doc-schema-') as tmp:
        store = Store(tmp, startup=False)
        try:
            fields = {row[1] for table in ('settings', 'api_keys', 'requests')
                      for row in store.db.execute('pragma table_info(' + table + ')')}
        finally:
            store.close()
    for field in sorted(fields | set(DEFAULTS)):
        if not re.search(r'(?<![\w])' + re.escape(field) + r'(?![\w])', documents['SCHEMA']):
            errors.append('Undocumented SQLite column or setting: ' + field)
    # AST literal sets avoid importing provider or jsonschema dependencies in CI.
    tree = ast.parse((root / 'desktop_bridge/contract.py').read_text(encoding='utf-8'))
    fields = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in
                ('SUPPORTED', 'NULLABLE_UNSUPPORTED', 'KNOWN') for t in node.targets):
            for child in ast.walk(node.value):
                if isinstance(child, ast.Set):
                    fields.update(ast.literal_eval(child))
    for field in sorted(fields):
        if not re.search(r'(?<![\w])' + re.escape(field) + r'(?![\w])', documents['API']):
            errors.append('Undocumented API field: ' + field)
    css = (root / 'desktop_bridge/web/style.css').read_text(encoding='utf-8')
    for token in sorted(set(re.findall(r'(--[a-z][a-z0-9-]*)\s*:', css))):
        if token not in documents['DESIGN-SYSTEM']:
            errors.append('Undocumented design token: ' + token)
    for name in ('README.md', 'AGENTS.md'):
        if 'docs/README.md' not in (root / name).read_text(encoding='utf-8'):
            errors.append(name + ' must link the product document index.')
    return errors


if __name__ == '__main__':
    failures = check()
    for failure in failures:
        print(failure)
    if failures:
        raise SystemExit(1)
    print('Product documents: schema, settings, API fields, design tokens and links covered.')
