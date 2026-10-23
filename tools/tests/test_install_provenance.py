import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from install import provenance

COMMIT = 'f5b56a8777329ba9a5fe3116e66c47ee66080083'
pytestmark = pytest.mark.skipif(not shutil.which('git'), reason='git required')


def repo(path):
    path.mkdir(parents=True, exist_ok=True)
    git = ['git', '-C', str(path), '-c', 'user.name=t', '-c', 'user.email=t@example.invalid']
    subprocess.run(git[:3] + ['init', '-q'], check=True)
    (path / 'file').write_text('x')
    subprocess.run(git + ['add', 'file'], check=True)
    subprocess.run(git + ['commit', '-qm', 'fixture'], check=True)
    return subprocess.check_output(git[:3] + ['rev-parse', 'HEAD'], text=True).strip()


def receipt(source, **changes):
    source.mkdir(parents=True, exist_ok=True)
    value = {'format': 'macos-byo-source', 'version': '0.9.6-mac.1', 'commit': COMMIT, **changes}
    (source / 'source-release.json').write_text(json.dumps(value))


def test_release_extracted_inside_unrelated_repository_uses_its_receipt(tmp_path):
    repo(tmp_path / 'outer')
    source = tmp_path / 'outer/.desktop-build/extracted/aigo-llm-bridge'
    receipt(source)
    assert provenance(source, '0.9.6-mac.1') == COMMIT


def test_mismatched_release_receipt_is_refused(tmp_path):
    receipt(tmp_path / 'source', version='0.9.5-mac.1')
    with pytest.raises(ValueError):
        provenance(tmp_path / 'source', '0.9.6-mac.1')


def test_checkout_root_reports_its_head_even_with_spaces_in_path(tmp_path):
    head = repo(tmp_path / 'AI EA MacOS/checkout')
    assert provenance(tmp_path / 'AI EA MacOS/checkout', '0.9.6-mac.1') == head


def test_unmarked_folder_inside_another_repository_has_no_commit(tmp_path):
    repo(tmp_path / 'outer')
    source = tmp_path / 'outer/copied-source'
    source.mkdir()
    assert provenance(source, '0.9.6-mac.1') is None
