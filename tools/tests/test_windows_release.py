"""Check executable publishing gates before a Windows release can reach GitHub."""
import ast
import os
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def test_publish_python_is_valid_and_windows_checks_native_format():
    text=(ROOT/'.github/workflows/desktop-publish.yml').read_text(encoding='utf-8')
    lines=text.splitlines()
    start=next(i for i,line in enumerate(lines) if "python - \"$TARGET\" <<'PY'" in line)+1
    end=next(i for i in range(start,len(lines)) if lines[i].strip()=='PY')
    script='\n'.join(line[10:] for line in lines[start:end])
    ast.parse(script)
    assert "manifest['sha256']" in script and "manifest['commit'] == commit" in script
    assert "manifest['format'] == 'windows-native-byo'" in script
    assert "manifest['requires_python'] is False" in script


def test_windows_build_requires_same_runtime_version_and_no_cloud_credentials():
    text=(ROOT/'.github/workflows/desktop-windows.yml').read_text(encoding='utf-8')
    assert 'tools/check_byo_package.py' in text and 'desktop_bridge/tests' in text
    assert 'cloudflare/test/relay.test.js' in text
    assert 'CLOUDFLARE_API_TOKEN' not in text and 'wrangler deploy' not in text
    assert "__version__!=version" in (ROOT/'packaging/windows/build.py').read_text(encoding='utf-8')


def test_mac_candidate_does_not_create_release_or_tag(tmp_path):
    text = (ROOT/'.github/workflows/release.yml').read_text(encoding='utf-8')
    script = text.split('          version=$(head', 1)[1]
    script = 'version=$(head' + '\n'.join(line[10:] if line.startswith('          ') else line
                                          for line in script.splitlines())
    (tmp_path/'VERSION').write_text('0.6.6-mac.1\n')
    # Fail immediately if either publishing tool is reached by the actual step.
    bin_dir = tmp_path/'bin'
    bin_dir.mkdir()
    for tool in ('git', 'gh', 'python'):
        stub = bin_dir/tool
        stub.write_text('#!/bin/sh\necho unexpected publication >&2\nexit 91\n')
        stub.chmod(0o700)
    result = subprocess.run(['bash', '-eu', '-c', script], cwd=tmp_path,
                            env={**os.environ, 'PATH': str(bin_dir)+os.pathsep+os.environ['PATH']},
                            text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert 'no tag or Release publication' in result.stdout
    assert not result.stderr
