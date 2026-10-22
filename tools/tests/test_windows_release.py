"""Check executable publishing gates before a Windows release can reach GitHub."""
import ast
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
