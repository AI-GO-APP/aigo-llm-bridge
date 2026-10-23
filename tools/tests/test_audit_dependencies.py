import importlib.util
import json
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('audit_dependencies',Path(__file__).resolve().parents[1]/'audit_dependencies.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def test_gate_inventories_pins_and_nested_npm_packages_without_local_settings(tmp_path):
    (tmp_path/'packaging/windows').mkdir(parents=True);(tmp_path/'cloudflare').mkdir()
    (tmp_path/'packaging/windows/requirements-lock.txt').write_text('certifi==2026.10.19 \\\n    --hash=sha256:synthetic\n')
    (tmp_path/'cloudflare/package-lock.json').write_text(json.dumps({'packages':{'':{'name':'private'},'node_modules/a/node_modules/b':{'version':'1.2.3'}}}))
    rows=audit.queries(tmp_path)
    assert any(row['package']=={'ecosystem':'npm','name':'b'} for row in rows)
    assert any(row['version']=='2026.10.19' for row in rows)
    assert all(set(row)=={'package','version'} for row in rows)


def test_gate_rejects_incomplete_database_response(monkeypatch):
    class Response:
        def __enter__(self):return self
        def __exit__(self,*_):pass
        def read(self,*_):return b'{"results":[]}'
    monkeypatch.setattr(audit.urllib.request,'build_opener',lambda *_:type('Opener',(),{'open':lambda *_args,**_kwargs:Response()})())
    with pytest.raises(ValueError,match='Incomplete'):audit.audit([{'package':{'ecosystem':'PyPI','name':'certifi'},'version':'synthetic'}])
