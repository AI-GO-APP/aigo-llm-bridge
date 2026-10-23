import importlib.util
from pathlib import Path
import subprocess

import pytest

spec = importlib.util.spec_from_file_location('windows_build_resources', Path(__file__).resolve().parents[1] / 'build_resources.py')
resources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resources)


def test_installer_does_not_absorb_other_platform_code_or_private_reports(tmp_path, monkeypatch):
    root = tmp_path / 'repo'
    root.mkdir()
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    (root / 'guide.md').write_text('[other](other.md#section)\n[local](local.md)\n```\n[example](missing.md)\n```')
    (root / 'local.md').write_text('Local guide')
    (root / 'other.md').write_text('Other platform instructions')
    subprocess.run(['git', 'add', '.'], cwd=root, check=True)
    monkeypatch.setattr(resources, 'DOCUMENTS', ('guide.md', 'local.md'))
    stage = tmp_path / 'stage'
    resources.stage_documents(root, stage, 'a' * 40)
    text = (stage / 'documents/guide.md').read_text()
    assert 'https://github.com/AI-GO-APP/local-token-buffet-bridge/blob/' + 'a' * 40 + '/other.md#section' in text
    assert '[local](local.md)' in text and '[example](missing.md)' in text
    assert not (stage / 'documents/other.md').exists()
    (root / 'private.md').write_text('Owner-only evidence')
    (root / 'guide.md').write_text('[private](private.md)')
    with pytest.raises(ValueError, match='untracked'):
        resources.stage_documents(root, stage, 'a' * 40)
    (root / 'guide.md').write_text('[outside](../outside.md)')
    with pytest.raises(ValueError, match='external'):
        resources.stage_documents(root, stage, 'a' * 40)
